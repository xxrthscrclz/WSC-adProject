from .models import DayOfWeek

DEFAULT_GRID_START_HOUR = 9
DEFAULT_GRID_END_HOUR = 18

DAY_LABELS = [label for _, label in DayOfWeek.choices]


def _time_to_minutes(value):
    return value.hour * 60 + value.minute


def compute_grid_range(schedules):
    start_hour = DEFAULT_GRID_START_HOUR
    end_hour = DEFAULT_GRID_END_HOUR

    for schedule in schedules:
        if schedule.start_time.hour < start_hour:
            start_hour = schedule.start_time.hour

        if schedule.end_time.minute > 0:
            needed_end = schedule.end_time.hour + 1
        else:
            needed_end = schedule.end_time.hour
        end_hour = max(end_hour, needed_end)

    if end_hour <= start_hour:
        end_hour = start_hour + 1

    return start_hour, end_hour


def build_weekly_grid(schedules, force_start=None, force_end=None):
    start_hour, end_hour = compute_grid_range(schedules)
    if force_start is not None:
        start_hour = min(start_hour, force_start)
    if force_end is not None:
        end_hour = max(end_hour, force_end)

    if end_hour <= start_hour:
        end_hour = start_hour + 1

    total_minutes = (end_hour - start_hour) * 60
    hours = [{"hour": hour, "label": f"{hour:02d}:00"} for hour in range(start_hour, end_hour)]

    blocks = []
    for index, schedule in enumerate(schedules):
        start_minutes = _time_to_minutes(schedule.start_time) - start_hour * 60
        end_minutes = _time_to_minutes(schedule.end_time) - start_hour * 60
        duration = max(end_minutes - start_minutes, 1)

        blocks.append(
            {
                "schedule": schedule,
                "day": schedule.day_of_week,
                "top_pct": start_minutes / total_minutes * 100,
                "height_pct": duration / total_minutes * 100,
                "color_index": index % 6,
            }
        )

    days = []
    for day_index, label in enumerate(DAY_LABELS):
        days.append(
            {
                "index": day_index,
                "label": label,
                "blocks": [block for block in blocks if block["day"] == day_index],
            }
        )

    return {
        "hours": hours,
        "days": days,
        "start_hour": start_hour,
        "end_hour": end_hour,
        "row_count": end_hour - start_hour,
    }
