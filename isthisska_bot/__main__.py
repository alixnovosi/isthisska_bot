"""Main class for bot."""

import logging
import subprocess
import sys
import time
from logging.handlers import RotatingFileHandler

import album_art_gen
import send
import tweepy

# Delay between tweets in seconds.
DELAY = 3600
ALBUM_ART_FILENAME = album_art_gen.ALBUM_ART_FILENAME
TWEET_TEXT = "Is this ska?"


def set_up_logging():
    """Set up proper logging."""
    logger = logging.getLogger("root")
    logger.setLevel(logging.DEBUG)

    # Log everything verbosely to a file.
    file_handler = RotatingFileHandler(filename="log", maxBytes=1024000000, backupCount=10)
    verbose_form = logging.Formatter(fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s")
    file_handler.setFormatter(verbose_form)
    file_handler.setLevel(logging.DEBUG)
    logger.addHandler(file_handler)

    # Provide a stdout handler logging at INFO.
    stream_handler = logging.StreamHandler(sys.stdout)
    simple_form = logging.Formatter(fmt="%(message)s")
    stream_handler.setFormatter(simple_form)
    stream_handler.setLevel(logging.INFO)

    logger.addHandler(stream_handler)

    return logger

if __name__ == "__main__":
    api = send.auth_and_get_api()

    LOG = set_up_logging()

    while True:
        LOG.info("Grabbing random album art from Musicbrainz\n.")
        album_art_gen.produce_random_album_art()

        LOG.info("Sending tweet with art\n.")

        try:
            api.update_with_media(ALBUM_ART_FILENAME, status=TWEET_TEXT)

        except tweepy.TweepError as e:
            if hasattr(e, "reason") and "File is too big" in e.reason:
                # Image is too big to tweet. Shrink and retry.
                LOG.info("Running shrink commands.\n")
                subprocess.run(["convert", ALBUM_ART_FILENAME, "-resize", "50%",
                                "smaller" + ALBUM_ART_FILENAME])
                subprocess.run(["mv", "smaller" + ALBUM_ART_FILENAME, ALBUM_ART_FILENAME])

                LOG.info("Retrying tweet.\n")

                api.update_with_media(ALBUM_ART_FILENAME, status=TWEET_TEXT)

            else:
                LOG.critical("A Tweepy error we don't know how to handle happened.\n")
                LOG.critical("Error reason: {}".format(e.reason))
                LOG.critical("Exiting.")
                break

        LOG.info("Sleeping for {} seconds.\n".format(DELAY))
        time.sleep(DELAY)
