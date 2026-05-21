import os

from config.util import strtobool

from .features import *  # noqa: F403
from .production import *  # noqa: F403

DEBUG: bool = strtobool(os.getenv("DEBUG", "False"))

SENTRY_SAMPLE_RATE = float(os.getenv("SENTRY_SAMPLE_RATE", "0.25"))
