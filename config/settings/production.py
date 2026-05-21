import json
import os
from sysconfig import get_path

from django.core.exceptions import ImproperlyConfigured
from django.utils.csp import CSP

from config.util import strtobool

from .features import *  # noqa: F403

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")
USE_X_FORWARDED_HOST = strtobool(os.getenv("USE_X_FORWARDED_HOST", "False"))

# Application definition
INSTALLED_APPS = [
    "app.hospitaldetails",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.jinja2.Jinja2",
        "DIRS": [
            os.path.join(BASE_DIR, "app/templates"),
            os.path.join(get_path("platlib"), "tna_frontend_jinja/templates"),
        ],
        "APP_DIRS": True,
        "OPTIONS": {
            "environment": "config.jinja2.environment",
        },
    },
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

SENTRY_DSN = os.getenv("SENTRY_DSN", "")
SENTRY_SAMPLE_RATE = float(os.getenv("SENTRY_SAMPLE_RATE", "0.1"))

# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DATABASE_NAME", ""),
        "USER": os.environ.get("DATABASE_USER", ""),
        "PASSWORD": os.environ.get("DATABASE_PASSWORD", ""),
        "HOST": os.environ.get("DATABASE_HOST", ""),
        "PORT": os.environ.get("DATABASE_PORT", "5432"),
    }
}

# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = "en-gb"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.0/howto/static-files/

STATIC_URL = "static/"
STATIC_ROOT = os.path.join(BASE_DIR, "static")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "app", "static")]
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# TNA Configuration

ENVIRONMENT_NAME: str = os.environ.get("ENVIRONMENT_NAME", "production")
CONTAINER_IMAGE: str = os.environ.get("CONTAINER_IMAGE", "")
BUILD_VERSION: str = os.environ.get("BUILD_VERSION", "")
TNA_FRONTEND_VERSION: str = ""
try:
    with open(
        os.path.join(
            os.path.realpath(os.path.dirname(__file__)),
            "node_modules/@nationalarchives/frontend",
            "package.json",
        )
    ) as package_json:
        try:
            data = json.load(package_json)
            TNA_FRONTEND_VERSION = data["version"] or ""
        except ValueError:
            pass
except FileNotFoundError:
    pass

SECRET_KEY: str = os.environ.get("SECRET_KEY", "")
if not SECRET_KEY:
    raise ImproperlyConfigured(
        "SECRET_KEY environment variable must be set and cannot be empty."
    )

DEBUG: bool = False

COOKIE_DOMAIN: str = os.environ.get("COOKIE_DOMAIN", ".nationalarchives.gov.uk")
COOKIE_PREFERENCES_URL: str = os.environ.get("COOKIE_PREFERENCES_URL", "/cookies/")
COOKIE_PREFERENCES_KEY: str = os.environ.get(
    "COOKIE_PREFERENCES_KEY", "dontShowCookieNotice"
)

CSP_REPORT_URL: str = os.environ.get("CSP_REPORT_URL", "")
if CSP_REPORT_URL:
    CSP_REPORT_URL += f"&sentry_release={BUILD_VERSION}" if BUILD_VERSION else ""
SECURE_CSP = {
    "default-src": [CSP.SELF],
    "base-uri": [CSP.NONE],
    "object-src": [CSP.NONE],
    "img-src": os.environ.get("CSP_IMG_SRC", CSP.SELF).split(","),
    "script-src": os.environ.get("CSP_SCRIPT_SRC", CSP.SELF).split(","),
    "style-src": os.environ.get("CSP_STYLE_SRC", CSP.SELF).split(","),
    "font-src": os.environ.get("CSP_FONT_SRC", CSP.SELF).split(","),
    "connect-src": os.environ.get("CSP_CONNECT_SRC", CSP.SELF).split(","),
    "media-src": os.environ.get("CSP_MEDIA_SRC", CSP.SELF).split(","),
    "worker-src": os.environ.get("CSP_WORKER_SRC", CSP.SELF).split(","),
    "frame-src": os.environ.get("CSP_FRAME_SRC", CSP.SELF).split(","),
    "report-uri": CSP_REPORT_URL or None,
}

GA4_ID = os.environ.get("GA4_ID", "")
