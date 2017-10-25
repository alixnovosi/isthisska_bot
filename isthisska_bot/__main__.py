"""Main class for bot."""

import os
import subprocess
import time

import botskeleton
import tweepy

import album_art_gen

# Delay between tweets in seconds.
DELAY = 1800 # half hour
ALBUM_ART_FILENAME = album_art_gen.ALBUM_ART_FILENAME
TWEET_TEXT = "Is this ska?\n(MB Release: https://musicbrainz.org/release/{})"

if __name__ == "__main__":
    SECRETS_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "SECRETS")
    api = botskeleton.BotSkeleton(SECRETS_DIR, bot_name="isthisska_bot")

    LOG = botskeleton.set_up_logging()

    while True:
        LOG.info("Grabbing random album art from Musicbrainz.")
        try:
            id = album_art_gen.produce_random_album_art()

        except album_art_gen.APIException as e:
            LOG.error("Encountered an API Exception.")
            LOG.error(f"Code: {e.code} Message: {e.message}")

            if e.code == 503:
                LOG.error("API error or rate limiting - waiting at least a few minutes.")
                time.sleep(300)
            LOG.error("Restarting from the beginning.")
            continue

        LOG.info("Sending tweet with art.")

        try:
            api.send_with_one_media(TWEET_TEXT.format(id), ALBUM_ART_FILENAME)

        except tweepy.TweepError as e:
            if hasattr(e, "reason") and "File is too big" in e.reason:
                # Image is too big to tweet. Shrink and retry.
                LOG.info("Running shrink commands.")
                subprocess.run(["convert", ALBUM_ART_FILENAME, "-resize", "50%",
                                "smaller" + ALBUM_ART_FILENAME])
                subprocess.run(["mv", "smaller" + ALBUM_ART_FILENAME, ALBUM_ART_FILENAME])

                LOG.info("Retrying tweet.")

                api.send_with_one_media(ALBUM_ART_FILENAME, status=TWEET_TEXT)

            else:
                LOG.critical("A Tweepy error we don't know how to handle happened.")
                LOG.critical(f"Error reason: {e.reason}")
                LOG.critical("Exiting.")
                break

        LOG.info(f"Sleeping for {DELAY} seconds.")
        time.sleep(DELAY)
