from django.urls import path

from . import views

app_name = "hospitaldetails"

urlpatterns = [
    path("search", views.search, name="search"),
    path("hospital/<int:id>/", views.hospital_detail, name="hospital_detail"),
    path("repository/<int:id>/", views.repository_detail, name="repository_detail"),
]
