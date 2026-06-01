from datetime import datetime

from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from reservations.models import Reservation, ReservationStatus
from reservations.services import ReservationService

from .models import StudyRoom


def _parse_date_param(date_str, default):
    if not date_str:
        return default
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return default


def _get_room_availability_for_date(room, reservation_date):
    seats = room.seats.filter(is_active=True)
    total = seats.count()
    if total == 0:
        return {"total": 0, "available": 0, "reserved": 0}

    reserved_seat_ids = set(
        Reservation.objects.filter(
            seat__in=seats,
            date=reservation_date,
            status=ReservationStatus.CONFIRMED,
        ).values_list("seat_id", flat=True)
    )
    reserved = len(reserved_seat_ids)
    return {"total": total, "available": total - reserved, "reserved": reserved}


def room_list(request):
    rooms = StudyRoom.objects.filter(is_active=True)
    room_items = [
        {"room": room, "availability": ReservationService.get_room_availability_now(room)}
        for room in rooms
    ]
    return render(request, "rooms/list.html", {"room_items": room_items})


def room_detail(request, room_id):
    room = get_object_or_404(StudyRoom, pk=room_id, is_active=True)
    today = timezone.localdate()
    selected_date = _parse_date_param(request.GET.get("date"), today)
    is_today = selected_date == today

    seats = room.seats.filter(is_active=True).order_by("seat_number")
    seat_ids = seats.values_list("id", flat=True)

    date_reservations = Reservation.objects.filter(
        seat_id__in=seat_ids,
        date=selected_date,
        status=ReservationStatus.CONFIRMED,
    ).order_by("start_time")

    reservations_by_seat = {}
    for reservation in date_reservations:
        reservations_by_seat.setdefault(reservation.seat_id, []).append(reservation)

    seat_items = []
    for seat in seats:
        seat_reservations = reservations_by_seat.get(seat.id, [])
        slots = [
            {
                "reservation": reservation,
                "status": ReservationService.get_reservation_slot_status(
                    reservation, selected_date
                ),
            }
            for reservation in seat_reservations
        ]
        active_reservation = (
            ReservationService.get_active_reservation(seat, selected_date)
            if is_today
            else None
        )
        has_reservations = bool(seat_reservations)

        if is_today:
            status_label = "사용 중" if active_reservation else "예약 가능"
            status_variant = "busy" if active_reservation else "available"
        elif has_reservations:
            status_label = "예약 있음"
            status_variant = "booked"
        else:
            status_label = "비어 있음"
            status_variant = "available"

        seat_items.append(
            {
                "seat": seat,
                "active_reservation": active_reservation,
                "display_slots": slots,
                "has_reservations": has_reservations,
                "status_label": status_label,
                "status_variant": status_variant,
            }
        )

    availability = _get_room_availability_for_date(room, selected_date)

    return render(
        request,
        "rooms/detail.html",
        {
            "room": room,
            "seat_items": seat_items,
            "availability": availability,
            "selected_date": selected_date.isoformat(),
            "is_today": is_today,
        },
    )
