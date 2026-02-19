import json
import re
from datetime import datetime

from django import template
from django.conf import settings
from django.templatetags.static import StaticNode
from django.urls import reverse
from django.utils.safestring import mark_safe
from jinja2 import Environment
from markupsafe import Markup

register = template.Library()


class StaticNodeWithVersion(StaticNode):
    @classmethod
    def handle_simple(cls, path, **kwargs):
        url = super().handle_simple(path)
        if kwargs:
            url += "?" + "&".join(
                [f"{parameter}={kwargs[parameter]}" for parameter in kwargs]
            )
        return mark_safe(url)


@register.tag("static")
def do_static_with_version(parser, token):
    return StaticNodeWithVersion.handle_token(parser, token)


def static_with_version(path, **kwargs):
    return StaticNodeWithVersion.handle_simple(path, **kwargs)


def slugify(s):
    if not s:
        return s
    s = s.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s


def now_iso_8601():
    now = datetime.now()
    now_date = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    return now_date


def linebreaksbr(text):
    """Convert newlines to <br> tags."""
    if not text:
        return text
    return mark_safe(text.replace("\n", "<br>"))


ABBR_PATTERNS = [
    {
        "pattern": r"\bc\.(\s*\d{1,4})",
        "title": "circa",
        "abbr": "c.",
        "suffix_group": 1,
    },
    {
        "pattern": r"\b(PLI)(\s*:)",
        "title": "Poor Law Institution",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(LA)(\s*:)",
        "title": "Local Authority",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {"pattern": r"\b(AC)(\s*:)", "title": "Acute", "abbr_group": 1, "suffix_group": 2},
    {
        "pattern": r"\b(GER)(\s*:)",
        "title": "Geriatric",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(LRO)(\s*:)",
        "title": "Local Record Office",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(AR)(\s*:)",
        "title": "Repository",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(NRA)(\s*:)",
        "title": "National Register of Archives",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(C)(\s*:)",
        "title": "Children",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(CAT)(\s*:)",
        "title": "Catalogue",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(VOL)(\s*:)",
        "title": "Voluntary",
        "abbr_group": 1,
        "suffix_group": 2,
    },
    {
        "pattern": r"\b(MNT)(\s*:)",
        "title": "Mental",
        "abbr_group": 1,
        "suffix_group": 2,
    },
]


def abbr(value):
    if not value:
        return value

    text = str(value)
    changed = False
    for rule in ABBR_PATTERNS:

        def replacer(match):
            if "abbr" in rule:
                abbreviation = rule["abbr"]
            else:
                abbreviation = match.group(rule["abbr_group"])
            suffix = ""
            if "suffix_group" in rule:
                suffix = match.group(rule["suffix_group"])
            return f'<abbr title="{rule["title"]}">{abbreviation}</abbr>{suffix}'

        text, replacements = re.subn(rule["pattern"], replacer, text)
        if replacements:
            changed = True

    if changed:
        return mark_safe(text)
    if isinstance(value, Markup):
        return value
    return text


def environment(**options):
    env = Environment(**options)

    TNA_FRONTEND_VERSION = ""
    try:
        with open(
            "/app/node_modules/@nationalarchives/frontend/package.json",
        ) as package_json:
            try:
                data = json.load(package_json)
                TNA_FRONTEND_VERSION = data["version"] or ""
            except ValueError:
                pass
    except FileNotFoundError:
        pass

    env.globals.update(
        {
            "static": static_with_version,
            "app_config": {
                "ENVIRONMENT_NAME": settings.ENVIRONMENT_NAME,
                "GA4_ID": settings.GA4_ID,
                "CONTAINER_IMAGE": settings.CONTAINER_IMAGE,
                "BUILD_VERSION": settings.BUILD_VERSION,
                "TNA_FRONTEND_VERSION": TNA_FRONTEND_VERSION,
                "COOKIE_DOMAIN": settings.COOKIE_DOMAIN,
            },
            "url_for": reverse,
            "now_iso_8601": now_iso_8601,
        }
    )
    env.filters.update({"slugify": slugify, "linebreaksbr": linebreaksbr, "abbr": abbr})
    return env
