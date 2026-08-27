import os
import sys

from tna_utilities import strtobool

from .features import *  # noqa: F403
from .production import *  # noqa: F403

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "*").split(",")

DEBUG: bool = strtobool(os.getenv("DEBUG", "False"))

SENTRY_SAMPLE_RATE = float(os.getenv("SENTRY_SAMPLE_RATE", "1.0"))

IS_TESTING = any(
    arg in {"test", "pytest"} for arg in sys.argv
)  # Bypass debug toolbar when running tests, DJDT can't be used with tests (debug_toolbar.E001)
if DEBUG and not IS_TESTING:
    try:
        import debug_toolbar  # noqa: F401

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
