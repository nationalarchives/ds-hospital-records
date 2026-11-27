import json
import logging
from urllib.parse import unquote

from django.http.cookie import parse_cookie

from app.lib.wagtail_api import get_wagtail_api_notifications

logger = logging.getLogger(__name__)


def wagtail_notifications(request):
    dismissed_notifications = []
    for part in request.META.get("HTTP_COOKIE", "").split(";"):
        cookie = parse_cookie(part).get("dismissed_notifications")
        if not cookie:
            continue
        try:
            values = json.loads(unquote(cookie))
            if not isinstance(values, list) or not all(
                isinstance(uid, str) or type(uid) is int for uid in values
            ):
                raise ValueError("Expected a list of notification IDs")
            dismissed_notifications.extend(str(uid) for uid in values)
        except ValueError as exc:
            logger.warning("Invalid dismissed notifications cookie: %s", exc)

    return {
        "wagtail_notifications": get_wagtail_api_notifications(),
        "dismissed_notifications": dismissed_notifications,
    }
