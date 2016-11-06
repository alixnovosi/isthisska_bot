"""Main class for bot."""

import subprocess
import time

import album_art_gen
import send
import tweepy

# Delay between tweets in seconds.
DELAY = 3600
ALBUM_ART_FILENAME = album_art_gen.ALBUM_ART_FILENAME

if __name__ == "__main__":
    api = send.auth_and_get_api()

    with open("log", "w") as f:
        while True:
            f.write("Grabbing random album art from Musicbrainz\n.")
            f.flush()
            album_art_gen.produce_random_album_art()

            f.write("Sending tweet with art\n.")
            f.flush()

            try:
                api.update_with_media(ALBUM_ART_FILENAME, status="Is this ska?")

            except tweepy.TweepError as e:
                if hasattr(e, "reason") and "File is too big" in e.reason:
                    # Image is too big to tweet. Shrink and retry.
                    f.write("Running shrink commands.\n")
                    f.flush()
                    subproccess.run(["convert", ALBUM_ART_FILENAME, "-resize", "50%",
                                     "smaller" + ALBUM_ART_FILENAME])
                    subprocess.run(["mv", "smaller" + ALBUM_ART_FILENAME, ALBUM_ART_FILENAME])

                    f.write("Retrying tweet.\n")
                    f.flush()

                    api.update_with_media(ALBUM_ART_FILENAME, status="Is this ska?")



                else:
                    f.write("A Tweepy error we don't know how to handle happened.\n")
                    f.write("Error reason: {}".format(e.reason))
                    f.flush()
                    break


            f.write("Sleeping for {} seconds.\n".format(DELAY))
            f.flush()
            time.sleep(DELAY)
