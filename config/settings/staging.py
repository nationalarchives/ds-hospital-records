import os

from config.util import strtobool

from .features import *
from .production import *

DEBUG: bool = strtobool(os.getenv("DEBUG", "False"))
