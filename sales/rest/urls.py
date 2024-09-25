from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("quote/", views.create_quote, name="create_quote"),
]