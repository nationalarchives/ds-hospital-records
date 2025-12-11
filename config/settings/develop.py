import os

from config.util import strtobool

from .features import *
from .production import *

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

DEBUG: bool = strtobool(os.getenv("DEBUG", "False"))

if DEBUG:
    try:
        import debug_toolbar

        INSTALLED_APPS += [  # noqa: F405
            "debug_toolbar",
        ]

        MIDDLEWARE = [
            "debug_toolbar.middleware.DebugToolbarMiddleware",
        ] + MIDDLEWARE  # noqa: F405

        DEBUG_TOOLBAR_CONFIG = {
            "SHOW_TOOLBAR_CALLBACK": lambda request: True,
            "SHOW_COLLAPSED": True,
        }
    except ImportError:
        pass
