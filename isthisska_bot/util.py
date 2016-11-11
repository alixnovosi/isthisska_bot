"""Util functions for isthisska_bot."""
import logging
import time
import sys
from logging.handlers import RotatingFileHandler

LOG = logging.getLogger("root")

LAST_CALLED = {}


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


# TODO stolen from puckfetcher - should pull out into a lib.
# Modified from https://stackoverflow.com/a/667706
def rate_limited(max_per_hour, *args):
    """Decorator to limit function to N calls/hour."""
    min_interval = 3600.0 / float(max_per_hour)

    def _decorate(func):
        things = [func.__name__]
        things.extend(args)
        key = "".join(things)
        LOG.debug("Rate limiter called for %s.", key)
        if key not in LAST_CALLED:
            LOG.debug("Initializing entry for %s.", key)
            LAST_CALLED[key] = 0.0

        def _rate_limited_function(*args, **kargs):
            last_called = LAST_CALLED[key]
            now = time.time()
            elapsed = now - last_called
            remaining = min_interval - elapsed
            LOG.debug("Rate limiter last called for '%s' at %s.", key, last_called)
            LOG.debug("Remaining cooldown time for '%s' is %s.", key, remaining)

            if remaining > 0 and last_called > 0.0:
                LOG.info("Self-enforced rate limit hit, sleeping %s seconds.", remaining)
                time.sleep(remaining)

            LAST_CALLED[key] = time.time()
            ret = func(*args, **kargs)
            LOG.debug("Updating rate limiter last called for %s to %s.", key, now)
            return ret

        return _rate_limited_function
    return _decorate
