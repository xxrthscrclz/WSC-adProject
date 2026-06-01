from django.urls import path

from . import views

app_name = "rooms"

urlpatterns = [
    path("", views.room_list, name="list"),
    path("<int:room_id>/", views.room_detail, name="detail"),
]
