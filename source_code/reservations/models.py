from django.conf import settings
from django.db import models

from rooms.models import Seat


class ReservationStatus(models.TextChoices):
    CONFIRMED = "confirmed", "확정"
    CANCELLED = "cancelled", "취소"


class Reservation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="예약자",
    )
    seat = models.ForeignKey(
        Seat,
        on_delete=models.CASCADE,
        related_name="reservations",
        verbose_name="좌석",
    )
    date = models.DateField("예약 날짜")
    start_time = models.TimeField("시작 시간")
    end_time = models.TimeField("종료 시간")
    status = models.CharField(
        "상태",
        max_length=20,
        choices=ReservationStatus.choices,
        default=ReservationStatus.CONFIRMED,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "start_time"]

    def __str__(self):
        return f"{self.user.username} · {self.seat} · {self.date}"
