import os

from config.util import strtobool

from .features import *
from .production import *

DEBUG: bool = strtobool(os.getenv("DEBUG", "False"))

SENTRY_SAMPLE_RATE = float(os.getenv("SENTRY_SAMPLE_RATE", "0.25"))
