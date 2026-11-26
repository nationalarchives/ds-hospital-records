# query "WAGTAIL_API_URL/notifications" to get the homepage notifications
"""
wagtail api /notifications response
{
    "global_alert": {
        "title": text,
        "message": richtext,
        "alert_level": text (low, medium, high),
        "cascade": boolean,
        "uid": uuid,
    },
    "mourning_notice": {
        "title": text,
        "message": richtext,
    },
}
"""

import logging

from django.conf import settings
from django.core.cache import cache
from requests import RequestException, get

from app.lib.constants import WAGTAIL_NOTIFICATIONS_CACHE_KEY

logger = logging.getLogger(__name__)


def get_wagtail_api_notifications() -> dict | None:
    """
    Fetch notifications from the Wagtail API.
    """
    data = cache.get(WAGTAIL_NOTIFICATIONS_CACHE_KEY)

    if data is not None:
        return data

    if not settings.WAGTAIL_API_URL or not settings.WAGTAIL_API_KEY:
        logger.error("WAGTAIL_API_URL and WAGTAIL_API_KEY must be configured.")
        return None

    try:
        response = get(
            f"{settings.WAGTAIL_API_URL}/globals/notifications",
            headers={"Authorization": f"Token {settings.WAGTAIL_API_KEY}"},
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except (RequestException, ValueError) as exc:
        logger.error("Failed to fetch Wagtail API notifications: %s", exc)
        return None

    cache.set(
        WAGTAIL_NOTIFICATIONS_CACHE_KEY,
        data,
        timeout=settings.WAGTAIL_API_CACHE_TIMEOUT,
    )
    return data
