"""Main class for bot."""

import subprocess
import time

import tweepy

import album_art_gen
import send
import util

# Delay between tweets in seconds.
DELAY = 1800 # half hour
ALBUM_ART_FILENAME = album_art_gen.ALBUM_ART_FILENAME
TWEET_TEXT = "Is this ska?"

if __name__ == "__main__":
    api = send.auth_and_get_api()

    LOG = util.set_up_logging()

    while True:
        LOG.info("Grabbing random album art from Musicbrainz.")
        try:
            album_art_gen.produce_random_album_art()

        except album_art_gen.APIException as e:
            LOG.error("Encountered an API Exception.")
            LOG.error("Code: %s Message: %s", e.code, e.message)

            if e.code == 503:
                LOG.error("API error or rate limiting - waiting at least a few minutes.")
                time.sleep(300)
            LOG.error("Restarting from the beginning.")
            continue

        LOG.info("Sending tweet with art.")

        try:
            api.update_with_media(ALBUM_ART_FILENAME, status=TWEET_TEXT)

        except tweepy.TweepError as e:
            if hasattr(e, "reason") and "File is too big" in e.reason:
                # Image is too big to tweet. Shrink and retry.
                LOG.info("Running shrink commands.")
                subprocess.run(["convert", ALBUM_ART_FILENAME, "-resize", "50%",
                                "smaller" + ALBUM_ART_FILENAME])
                subprocess.run(["mv", "smaller" + ALBUM_ART_FILENAME, ALBUM_ART_FILENAME])

                LOG.info("Retrying tweet.")

                api.update_with_media(ALBUM_ART_FILENAME, status=TWEET_TEXT)

            else:
                LOG.critical("A Tweepy error we don't know how to handle happened.")
                LOG.critical("Error reason: {}".format(e.reason))
                LOG.critical("Exiting.")
                break

        LOG.info("Sleeping for {} seconds.".format(DELAY))
        time.sleep(DELAY)
