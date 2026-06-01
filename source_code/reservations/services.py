from datetime import date, time

from django.db.models import Q

from timetable.models import ClassSchedule

from .exceptions import ScheduleConflictError, TimeOverlapError
from .models import Reservation, ReservationStatus


class ReservationService:
    """예약 생성·취소 및 중복 검사를 담당하는 서비스 계층."""

    @classmethod
    def create_reservation(cls, user, seat, reservation_date, start_time, end_time):
        if start_time >= end_time:
            raise ValueError("종료 시간은 시작 시간보다 늦어야 합니다.")

        cls._validate_no_seat_overlap(seat, reservation_date, start_time, end_time)
        cls._validate_no_schedule_conflict(user, reservation_date, start_time, end_time)

        return Reservation.objects.create(
            user=user,
            seat=seat,
            date=reservation_date,
            start_time=start_time,
            end_time=end_time,
        )

    @classmethod
    def cancel_reservation(cls, reservation, user):
        if reservation.user_id != user.id:
            raise PermissionError("본인 예약만 취소할 수 있습니다.")
        if reservation.status == ReservationStatus.CANCELLED:
            raise ValueError("이미 취소된 예약입니다.")

        reservation.status = ReservationStatus.CANCELLED
        reservation.save(update_fields=["status", "updated_at"])
        return reservation

    @classmethod
    def get_seat_status_map(cls, room, reservation_date, start_time, end_time):
        """특정 시간대 기준 좌석별 예약 여부를 반환."""
        reserved_seat_ids = cls._overlapping_reservations(
            reservation_date, start_time, end_time
        ).values_list("seat_id", flat=True)

        return {
            seat.id: seat.id in set(reserved_seat_ids)
            for seat in room.seats.filter(is_active=True)
        }

    @classmethod
    def _validate_no_seat_overlap(cls, seat, reservation_date, start_time, end_time):
        overlap = cls._overlapping_reservations(
            reservation_date, start_time, end_time
        ).filter(seat=seat)
        if overlap.exists():
            raise TimeOverlapError("해당 좌석은 선택한 시간대에 이미 예약되어 있습니다.")

    @classmethod
    def _validate_no_schedule_conflict(cls, user, reservation_date, start_time, end_time):
        day_of_week = reservation_date.weekday()
        schedules = ClassSchedule.objects.filter(user=user, day_of_week=day_of_week)

        for schedule in schedules:
            if cls._times_overlap(start_time, end_time, schedule.start_time, schedule.end_time):
                raise ScheduleConflictError(
                    f"수업 시간({schedule.subject_name})과 겹칩니다. 다른 시간을 선택해 주세요."
                )

    @classmethod
    def _overlapping_reservations(cls, reservation_date, start_time, end_time):
        return Reservation.objects.filter(
            date=reservation_date,
            status=ReservationStatus.CONFIRMED,
        ).filter(
            Q(start_time__lt=end_time) & Q(end_time__gt=start_time)
        )

    @staticmethod
    def _times_overlap(start_a: time, end_a: time, start_b: time, end_b: time) -> bool:
        return start_a < end_b and end_a > start_b
