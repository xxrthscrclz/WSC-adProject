from datetime import datetime, time, timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from rooms.models import Seat
from timetable.grid import build_weekly_grid
from timetable.models import ClassSchedule

from .exceptions import (
    PastReservationError,
    ReservationError,
    ScheduleConflictError,
    TimeOverlapError,
    UserTimeOverlapError,
)
from .models import Reservation
from .services import ReservationService


def _friendly_reservation_error(exc):
    if isinstance(exc, PastReservationError):
        return str(exc)
    if isinstance(exc, UserTimeOverlapError):
        return "동일한 시간대는 중복 예약할 수 없습니다."
    if isinstance(exc, TimeOverlapError):
        return "선택한 시간대에 이 좌석은 이미 예약되어 있습니다."
    if isinstance(exc, ScheduleConflictError):
        return str(exc)
    return str(exc)


def _default_reservation_fields():
    """오늘 날짜, 다음 정각 시작, 시작+1시간 종료."""
    now = timezone.localtime()
    start_dt = now.replace(minute=0, second=0, microsecond=0)
    if now >= start_dt:
        start_dt += timedelta(hours=1)
    end_dt = start_dt + timedelta(hours=1)

    return {
        "form_date": start_dt.date().isoformat(),
        "form_start_time": start_dt.strftime("%H:%M"),
        "form_end_time": end_dt.strftime("%H:%M"),
    }


def _parse_reservation_form(post_data):
    reservation_date = datetime.strptime(post_data.get("date"), "%Y-%m-%d").date()
    start_time = datetime.strptime(post_data.get("start_time"), "%H:%M").time()
    end_time = datetime.strptime(post_data.get("end_time"), "%H:%M").time()
    return reservation_date, start_time, end_time


def _parse_date_param(date_str):
    return datetime.strptime(date_str, "%Y-%m-%d").date()


TIMETABLE_START_HOUR = 9
TIMETABLE_END_HOUR = 23

USER_SLOT_COLORS = [
    "#6366f1",
    "#8b5cf6",
    "#ec4899",
    "#f97316",
    "#14b8a6",
    "#3b82f6",
    "#eab308",
    "#22c55e",
    "#f43f5e",
    "#06b6d4",
]


def _slot_end_time(hour):
    if hour + 1 < 24:
        return time(hour + 1, 0)
    return time(23, 59, 59)


def _times_overlap(start_a, end_a, start_b, end_b):
    return start_a < end_b and end_a > start_b


def _build_booked_slots(seat, reservation_date):
    reservations = ReservationService.get_seat_reservations_for_date(seat, reservation_date)
    return [
        {
            "reservation": reservation,
            "status": ReservationService.get_reservation_slot_status(reservation, reservation_date),
        }
        for reservation in reservations
    ]


def _build_hourly_timetable(
    booked_slots,
    current_user_id=None,
    start_hour=TIMETABLE_START_HOUR,
    end_hour=TIMETABLE_END_HOUR,
):
    user_colors = {}
    color_index = 0
    timeline = []
    seen_users = {}

    for hour in range(start_hour, end_hour):
        slot_start = time(hour, 0)
        slot_end = _slot_end_time(hour)
        entry = {
            "hour": hour,
            "label": f"{hour:02d}:00",
            "end_label": f"{hour + 1:02d}:00" if hour + 1 < 24 else "24:00",
            "status": "free",
            "user_name": None,
            "color": None,
            "is_mine": False,
        }

        for slot in booked_slots:
            reservation = slot["reservation"]
            if _times_overlap(
                reservation.start_time,
                reservation.end_time,
                slot_start,
                slot_end,
            ):
                user_id = reservation.user_id
                if user_id not in user_colors:
                    user_colors[user_id] = USER_SLOT_COLORS[color_index % len(USER_SLOT_COLORS)]
                    color_index += 1
                    seen_users[user_id] = reservation.user.username
                entry["status"] = slot["status"]
                entry["user_name"] = reservation.user.username
                entry["color"] = user_colors[user_id]
                entry["is_mine"] = user_id == current_user_id
                break

        timeline.append(entry)

    legend = [
        {"user_name": seen_users[user_id], "color": color}
        for user_id, color in user_colors.items()
    ]

    return timeline, legend


@login_required
def my_reservations(request):
    reservations = Reservation.objects.filter(user=request.user).select_related(
        "seat", "seat__room"
    )
    return render(request, "reservations/my_list.html", {"reservations": reservations})


@login_required
def create_reservation(request, seat_id):
    seat = get_object_or_404(Seat, pk=seat_id, is_active=True)
    error_message = None
    success_message = None
    form_fields = _default_reservation_fields()

    if request.method == "GET" and request.GET.get("date"):
        try:
            form_fields["form_date"] = _parse_date_param(request.GET["date"]).isoformat()
        except ValueError:
            pass

    if request.method == "GET" and request.GET.get("start_time"):
        form_fields["form_start_time"] = request.GET["start_time"]

    if request.method == "GET" and request.GET.get("end_time"):
        form_fields["form_end_time"] = request.GET["end_time"]

    if request.method == "POST":
        form_fields = {
            "form_date": request.POST.get("date", ""),
            "form_start_time": request.POST.get("start_time", ""),
            "form_end_time": request.POST.get("end_time", ""),
        }
        try:
            reservation_date, start_time, end_time = _parse_reservation_form(request.POST)
            ReservationService.create_reservation(
                user=request.user,
                seat=seat,
                reservation_date=reservation_date,
                start_time=start_time,
                end_time=end_time,
            )
            redirect_url = reverse("reservations:create", args=[seat.id])
            return redirect(f"{redirect_url}?success=1&date={reservation_date.isoformat()}")
        except ReservationError as exc:
            error_message = _friendly_reservation_error(exc)
        except ValueError as exc:
            error_message = str(exc)

    if request.method == "GET" and request.GET.get("success") == "1":
        success_message = "예약이 완료되었습니다!"

    reservation_date = datetime.strptime(form_fields["form_date"], "%Y-%m-%d").date()
    booked_slots = _build_booked_slots(seat, reservation_date)
    hourly_timetable, timetable_legend = _build_hourly_timetable(
        booked_slots,
        current_user_id=request.user.id,
    )
    class_schedules = ClassSchedule.objects.filter(user=request.user)
    class_grid = build_weekly_grid(class_schedules) if class_schedules.exists() else None

    return render(
        request,
        "reservations/create.html",
        {
            "seat": seat,
            "error_message": error_message,
            "success_message": success_message,
            "hourly_timetable": hourly_timetable,
            "timetable_legend": timetable_legend,
            "class_grid": class_grid,
            "has_class_schedules": class_schedules.exists(),
            "min_date": timezone.localdate().isoformat(),
            **form_fields,
        },
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

    return redirect("reservations:my_list")
