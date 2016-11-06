import random

import requests
from bs4 import BeautifulSoup

MB_API_ROOT = "http://musicbrainz.org/ws/2/"
RELEASE_ROOT = MB_API_ROOT + "release/?query="

COVER_ART_API_URL = "http://coverartarchive.org/release"

OWNER_URL = "https://github.com/andrewmichaud/isthisska_bot"
USER_AGENT = "isthisska_twitterbot/1.0" + OWNER_URL
HEADERS = {"User-Agent": USER_AGENT}

RELEASE_COUNT_DICT = {}

ALBUM_ART_FILENAME = "album_art.jpg"


def gen_dict(letter):
    """Generate count of releases in musicbrainz for letter search."""
    url = RELEASE_ROOT + "{}&limit=1".format(letter)
    print("URL to get count: {}.".format(url))
    resp = requests.get(url, headers=HEADERS)

    soup = BeautifulSoup(resp.text, "html.parser")
    release_list = soup.find("release-list")
    count = release_list.attrs["count"]

    print("Got count {}.".format(count))

    RELEASE_COUNT_DICT[letter] = count


def produce_random_album_art():
    """
    Retrieve a random piece of album art from MusicBrainz/Album Art Archive.
    Save it as album_art.jpg
    """
    # Get a random album.
    letter = random.choice("abcdefghijklmnopqrstuvwxyz")
    if letter not in RELEASE_COUNT_DICT:
        gen_dict(letter)

    count = RELEASE_COUNT_DICT[letter]

    # Try a few times - not all albums MusicBrainz lists has album art.
    for i in range(15):

        # Choose a random index into the releases.
        offset = random.choice(range(int(count) - 1))
        url = "{}{}&limit=1&offset={}".format(RELEASE_ROOT, letter, offset)
        print("URL to get a random release: {}.".format(url))
        resp = requests.get(url, headers=HEADERS)
        if resp.status_code != 200:
            print("Status not 200 - it's {}. Exiting.".format(resp.status_code))
            return

        # who needs error handling.
        # Get release MBID to pull up the album art.
        soup = BeautifulSoup(resp.text, "html.parser")
        release = soup.find("release")
        print("Release: {}".format(release))

        id = release.attrs["id"]
        print("Got release id {}.".format(id))

        # Get an image - at last!
        # Hit coverartarchive API to get the actual art.
        url = "{}/{}".format(COVER_ART_API_URL, id)
        print(url)
        resp = requests.get(url, headers=HEADERS)

        if resp.status_code == 404:
            print("Got 404!")
            continue

        # this doesn't seem fragile at all.
        data = resp.json()
        album_art_url = data["images"][0]["image"]

        with open(ALBUM_ART_FILENAME, "wb") as f:
            art_data = requests.get(album_art_url, headers=HEADERS)
            f.write(art_data.content)

        break
