from django.contrib import admin

from .models import Seat, StudyRoom


class SeatInline(admin.TabularInline):
    model = Seat
    extra = 1


@admin.register(StudyRoom)
class StudyRoomAdmin(admin.ModelAdmin):
    list_display = ("name", "building", "floor", "capacity", "is_active")
    list_filter = ("building", "is_active")
    search_fields = ("name", "building")
    inlines = [SeatInline]


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ("seat_number", "room", "is_active")
    list_filter = ("room", "is_active")
