"""Main class for bot."""

import time

import album_art_gen
import send

# Delay between tweets in seconds.
DELAY = 3600

if __name__ == "__main__":
    api = send.auth_and_get_api()

    with open("log", "w") as f:
        while True:
            f.write("Grabbing random album art from Musicbrainz\n.")
            f.flush()
            album_art_gen.produce_random_album_art()

            f.write("Sending tweet with art\n.")
            f.flush()
            api.update_with_media("album_art.jpg", status="Is this ska?")

            f.write("Sleeping for {} seconds.\n".format(DELAY))
            f.flush()
            time.sleep(DELAY)
