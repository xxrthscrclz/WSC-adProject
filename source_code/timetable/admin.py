from django.contrib import admin

from .models import ClassSchedule


@admin.register(ClassSchedule)
class ClassScheduleAdmin(admin.ModelAdmin):
    list_display = ("user", "day_of_week", "subject_name", "start_time", "end_time", "location")
    list_filter = ("day_of_week",)
