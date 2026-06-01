from datetime import datetime

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from rooms.models import Seat

from .exceptions import ReservationError
from .models import Reservation
from .services import ReservationService


def _parse_reservation_form(post_data):
    reservation_date = datetime.strptime(post_data.get("date"), "%Y-%m-%d").date()
    start_time = datetime.strptime(post_data.get("start_time"), "%H:%M").time()
    end_time = datetime.strptime(post_data.get("end_time"), "%H:%M").time()
    return reservation_date, start_time, end_time


@login_required
def my_reservations(request):
    reservations = Reservation.objects.filter(user=request.user)
    return render(request, "reservations/my_list.html", {"reservations": reservations})


@login_required
def create_reservation(request, seat_id):
    seat = get_object_or_404(Seat, pk=seat_id, is_active=True)
    error_message = None

    if request.method == "POST":
        try:
            reservation_date, start_time, end_time = _parse_reservation_form(request.POST)
            ReservationService.create_reservation(
                user=request.user,
                seat=seat,
                reservation_date=reservation_date,
                start_time=start_time,
                end_time=end_time,
            )
            return redirect("reservations:my_list")
        except ReservationError as exc:
            error_message = str(exc)
        except ValueError as exc:
            error_message = str(exc)

    return render(
        request,
        "reservations/create.html",
        {"seat": seat, "error_message": error_message},
    )


@login_required
def cancel_reservation(request, reservation_id):
    reservation = get_object_or_404(Reservation, pk=reservation_id, user=request.user)

    if request.method == "POST":
        try:
            ReservationService.cancel_reservation(reservation, request.user)
        except (PermissionError, ValueError):
            pass
        return redirect("reservations:my_list")

    return render(request, "reservations/cancel_confirm.html", {"reservation": reservation})
