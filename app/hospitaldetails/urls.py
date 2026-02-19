from django.urls import path

from . import views

app_name = "hospitaldetails"

urlpatterns = [
    path("", views.home_page, name="home_page"),
    path("hospitals", views.search, name="search"),
    path("hospitals/<int:id>", views.hospital_detail, name="hospital_detail"),
    path("repositories", views.repository_list, name="repository_list"),
    path("repositories/<int:id>", views.repository_detail, name="repository_detail"),
]
