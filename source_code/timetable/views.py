from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .grid import build_weekly_grid
from .models import ClassSchedule


@login_required
def schedule_list(request):
    schedules = ClassSchedule.objects.filter(user=request.user)
    grid = build_weekly_grid(schedules)
    return render(
        request,
        "timetable/list.html",
        {
            "schedules": schedules,
            "grid": grid,
        },
    )


@login_required
def schedule_add(request):
    class_schedules = ClassSchedule.objects.filter(user=request.user)

    if request.method == "POST":
        ClassSchedule.objects.create(
            user=request.user,
            day_of_week=int(request.POST.get("day_of_week")),
            start_time=request.POST.get("start_time"),
            end_time=request.POST.get("end_time"),
            subject_name=request.POST.get("subject_name"),
            location=request.POST.get("location", ""),
        )
        return redirect("timetable:list")

    return render(
        request,
        "timetable/add.html",
        {
            "class_grid": build_weekly_grid(class_schedules, force_start=8, force_end=23),
            "has_class_schedules": class_schedules.exists(),
        },
    )


@login_required
def schedule_delete(request, schedule_id):
    schedule = get_object_or_404(ClassSchedule, pk=schedule_id, user=request.user)
    if request.method == "POST":
        schedule.delete()
    return redirect("timetable:list")


@login_required
def study_recommend(request):
    from .recommendation import generate_recommendations

    result = generate_recommendations(request.user)
    return render(request, "timetable/recommend.html", {"recommendation": result})
