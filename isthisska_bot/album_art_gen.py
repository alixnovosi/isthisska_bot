import logging
import os
import random

import backoff
import botskeleton
import requests
from bs4 import BeautifulSoup


# CONSTANTS related to the APIs we need to use.
MB_API_ROOT = "https://musicbrainz.org/ws/2/"
RELEASE_ROOT = f"{MB_API_ROOT}release/?query="

COVER_ART_API_URL = "https://coverartarchive.org/release"

# Hits per hour.
CAA_RATE_LIMIT = 1800
MB_RATE_LIMIT = 1800

# Being a good citizen - produce a useful user_agent.
OWNER_URL = "https://github.com/andrewmichaud/isthisska_bot"
USER_AGENT = f"isthisska_twitterbot/1.0 ({OWNER_URL}) (bots+isthisska@mail.andrewmichaud.com)"
HEADERS = {"User-Agent": USER_AGENT}

# For caching(ish) results from MusicBrainz, and storing our eventual output image.
RELEASE_COUNT_DICT = {}
ALBUM_ART_FILENAME = "album_art.png"
HERE = os.path.abspath(os.path.dirname(__file__))
ALBUM_ART_PATH = os.path.join(HERE, ALBUM_ART_FILENAME)

# For blacklisting some albums.
BLACKLIST_FILENAME = "blacklist.txt"
SECRETS = os.path.join(HERE, "SECRETS")
BLACKLIST_PATH = os.path.join(SECRETS, BLACKLIST_FILENAME)

LOG = logging.getLogger("root")


def produce_random_album_art():
    """
    Retrieve a random piece of album art from MusicBrainz/Album Art Archive.
    Save it as album_art.png
    Return release id of album we found.
    """
    # Get a random album.
    letter = random.choice("abcdefghijklmnopqrstuvwxyz")
    if letter not in RELEASE_COUNT_DICT:
        gen_dict(letter)

    count = RELEASE_COUNT_DICT[letter]

    # Try a few times - not all albums MusicBrainz lists has album art.
    for i in range(15):

        # Get a random release.
        resp = perform_random_release_search(letter, count)
        if resp.status_code == 503:
            msg = "Rate limited, or other service error."
            LOG.error(msg)
            raise APIException(msg, resp.status_code)

        elif resp.status_code != 200:
            msg = f"Unhandled error - code {resp.status_code}. Exiting."
            LOG.error(msg)
            raise APIException(msg, resp.status_code)

        LOG.info("Performed release search, no issues.")

        # who needs error handling.
        # Get release MBID to pull up the album art.
        soup = BeautifulSoup(resp.text, "html.parser")
        release = soup.find("release")
        LOG.debug(f"Release: {release}")

        if release is None:
            raise APIException("Couldn't find release!")

        release_id = release.attrs["id"]
        LOG.info(f"Got release id {release_id}.")

        # See if release is blacklisted, if so skip.
        try:
            if release_id in open(BLACKLIST_PATH).read():
                LOG.error(f"Release {release_id} is blacklisted.")
                continue
        except FileNotFoundError:
            pass

        # for caption and message text.
        release_group = soup.find("release-group")
        album = "unknown"
        if release_group is not None:
            album = "".join(release_group.find("title").contents)

        artist_info = soup.find("artist")
        artist = "unknown"
        if artist_info is not None:
            artist = "".join(artist_info.find("name").contents)

        LOG.debug(f"Artist '{artist}' and album '{album}'")

        # Get an image - at last!
        resp = perform_album_art_search(release_id)
        if resp.status_code == 404:
            LOG.error("Got 404 trying to get album art!")
            continue

        # TODO this doesn't seem fragile at all.
        data = resp.json()
        album_art_url = data["images"][0]["image"]

        with open(ALBUM_ART_PATH, "wb") as f:
            art_data = get_image(album_art_url)
            f.write(art_data.content)

        break

    return {"release_id": release_id, "artist": artist, "album": album}


def gen_dict(letter):
    """Generate count of releases in musicbrainz for letter search."""
    resp = perform_letter_search(letter)
    soup = BeautifulSoup(resp.text, "html.parser")

    release_list = soup.find("release-list")
    if release_list is None:
        raise APIException("Couldn't find release!")

    count = release_list.attrs["count"]

    LOG.debug(f"Got count {count}.")

    RELEASE_COUNT_DICT[letter] = count


# Wrappers around API stuff - handle URLs and logic for how we hit MusicBrainz and Cover Art
# Archive.
def get_image(url):
    """Get image from URL we got from album art search."""
    return cover_art_archive_query(url)


def perform_album_art_search(release_id):
    """Get an actual piece of album art."""
    # Hit coverartarchive API to get the actual art.
    url = f"{COVER_ART_API_URL}/{release_id}"
    LOG.debug(f"Cover art API url: {url}")
    return cover_art_archive_query(url)


def perform_random_release_search(letter, count):
    """
    Get a random release from MusicBrainz.
    Do this by randomly pulling a release from the list returned by searching for a letter.
    """
    # Choose a random index into the releases.
    offset = random.choice(range(int(count) - 1))
    url = f"{RELEASE_ROOT}{letter}&limit=1&offset={offset}"
    LOG.debug(f"URL to get a random release: {url}.")
    return mb_query(url)


def perform_letter_search(letter):
    """Get results of search for a letter from MusicBrainz API."""
    url = f"{RELEASE_ROOT}{letter}&limit=1"
    LOG.debug("URL to get count: {url}.")
    return mb_query(url)


# Rate-limited functions to do the actual hitting.
# There's no rate limit on the Cover Art Archive, but be nice and stay at or below 2 requests a
# second.
@backoff.on_exception(backoff.expo,
                      requests.exceptions.Timeout,
                      max_tries=5)
@botskeleton.rate_limited(CAA_RATE_LIMIT)
def cover_art_archive_query(url, headers=HEADERS):
    """Perform rate-limited query against Cover Art Archive API."""
    return requests.get(url, headers=HEADERS)


@backoff.on_exception(backoff.expo,
                      requests.exceptions.Timeout,
                      max_tries=5)
@botskeleton.rate_limited(MB_RATE_LIMIT)
def mb_query(url, headers=HEADERS):
    """Perform rate-limited query against MusicBrainz API."""
    return requests.get(url, headers=headers)


# Other stuff.
class APIException(Exception):
    def __init__(self, message, code=None):
        super(APIException, self).__init__(message)

        self.message = message

        self.code = code
