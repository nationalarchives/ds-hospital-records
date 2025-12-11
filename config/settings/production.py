import json
import os
from pathlib import Path
from sysconfig import get_path

from config.util import strtobool
from csp.constants import NONE, SELF

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")
USE_X_FORWARDED_HOST = strtobool(os.getenv("USE_X_FORWARDED_HOST", "False"))

# Application definition
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "csp",
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
    "csp.middleware.CSPMiddleware",
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

LANGUAGE_CODE = "en-us"

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

DEBUG: bool = False

COOKIE_DOMAIN: str = os.environ.get("COOKIE_DOMAIN", "")

CSP_REPORT_URL: str = os.environ.get("CSP_REPORT_URL", "")
if CSP_REPORT_URL:
    CSP_REPORT_URL += f"&sentry_release={BUILD_VERSION}" if BUILD_VERSION else ""
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": [SELF],
        "base-uri": [NONE],
        "object-src": [NONE],
        "img-src": os.environ.get("CSP_IMG_SRC", SELF).split(","),
        "script-src": os.environ.get("CSP_SCRIPT_SRC", SELF).split(","),
        "style-src": os.environ.get("CSP_STYLE_SRC", SELF).split(","),
        "font-src": os.environ.get("CSP_FONT_SRC", SELF).split(","),
        "connect-src": os.environ.get("CSP_CONNECT_SRC", SELF).split(","),
        "media-src": os.environ.get("CSP_MEDIA_SRC", SELF).split(","),
        "worker-src": os.environ.get("CSP_WORKER_SRC", SELF).split(","),
        "frame-src": os.environ.get("CSP_FRAME_SRC", SELF).split(","),
        "report-uri": CSP_REPORT_URL or None,
    }
}

GA4_ID = os.environ.get("GA4_ID", "")
