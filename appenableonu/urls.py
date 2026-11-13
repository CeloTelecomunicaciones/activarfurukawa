from django.urls import path
from . import views

urlpatterns = [
    path("", views.main, name="main"),
    path("appenableonu/", views.habilitar_onu, name="habilitar_onu"),
]