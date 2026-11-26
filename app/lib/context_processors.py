from app.lib.wagtail_api import get_wagtail_api_notifications


def wagtail_notifications(request):
    return {"wagtail_notifications": get_wagtail_api_notifications()}
