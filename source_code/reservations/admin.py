from django.contrib import admin

from .models import Reservation


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ("user", "seat", "date", "start_time", "end_time", "status")
    list_filter = ("status", "date")
    search_fields = ("user__username", "seat__seat_number")
