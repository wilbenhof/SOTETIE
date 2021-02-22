from django.urls import path
from scripti import views

urlpatterns = [
    path("", views.home, name="home"),
]