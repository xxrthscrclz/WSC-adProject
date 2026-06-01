from django.conf import settings
from django.db import models


class DayOfWeek(models.IntegerChoices):
    MONDAY = 0, "월"
    TUESDAY = 1, "화"
    WEDNESDAY = 2, "수"
    THURSDAY = 3, "목"
    FRIDAY = 4, "금"
    SATURDAY = 5, "토"
    SUNDAY = 6, "일"


class ClassSchedule(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="class_schedules",
        verbose_name="사용자",
    )
    day_of_week = models.IntegerField("요일", choices=DayOfWeek.choices)
    start_time = models.TimeField("시작 시간")
    end_time = models.TimeField("종료 시간")
    subject_name = models.CharField("과목명", max_length=100)
    location = models.CharField("강의실", max_length=100, blank=True)

    class Meta:
        ordering = ["day_of_week", "start_time"]

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.subject_name}"
