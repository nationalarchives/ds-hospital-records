from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from app.hospitaldetails.models import Hospital


class StaticSitemap(Sitemap):
    priority = 1.0
    changefreq = "monthly"

    def items(self):
        return ["hospitaldetails:home_page"]

    def location(self, item):
        return reverse(item)


class HospitalSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.7

    def items(self):
        return Hospital.objects.all()

    def location(self, item):
        return reverse("hospitaldetails:hospital_detail", args=[item.pk])

    def lastmod(self, item):
        return item.last_updated_at
