from django.urls import path

from . import views

app_name = "reservations"

urlpatterns = [
    path("my/", views.my_reservations, name="my_list"),
    path("create/<int:seat_id>/", views.create_reservation, name="create"),
    path("<int:reservation_id>/cancel/", views.cancel_reservation, name="cancel"),
]
