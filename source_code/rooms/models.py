from django.db import models


class StudyRoom(models.Model):
    name = models.CharField("스터디룸 이름", max_length=100)
    building = models.CharField("건물", max_length=50)
    floor = models.PositiveSmallIntegerField("층")
    capacity = models.PositiveSmallIntegerField("좌석 수")
    description = models.TextField("설명", blank=True)
    is_active = models.BooleanField("사용 가능", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["building", "floor", "name"]

    def __str__(self):
        return f"{self.building} {self.floor}F · {self.name}"


class Seat(models.Model):
    room = models.ForeignKey(
        StudyRoom,
        on_delete=models.CASCADE,
        related_name="seats",
        verbose_name="스터디룸",
    )
    seat_number = models.CharField("좌석 번호", max_length=20)
    is_active = models.BooleanField("사용 가능", default=True)

    class Meta:
        ordering = ["room", "seat_number"]
        unique_together = [["room", "seat_number"]]

    def __str__(self):
        return f"{self.room.name} · {self.seat_number}번"
