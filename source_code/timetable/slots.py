from datetime import date, datetime, time, timedelta

from django.utils import timezone

from reservations.models import Reservation, ReservationStatus

STUDY_DAY_START = time(9, 0)
STUDY_DAY_END = time(23, 0)
MIN_SLOT_MINUTES = 60
LOOKAHEAD_DAYS = 7
MAX_RECOMMENDATIONS = 5

DAY_LABELS = ["월", "화", "수", "목", "금", "토", "일"]


def _time_to_minutes(value):
    return value.hour * 60 + value.minute


def _minutes_to_time(minutes):
    minutes = max(0, min(minutes, 23 * 60 + 59))
    return time(minutes // 60, minutes % 60)


def _times_overlap(start_a, end_a, start_b, end_b):
    return start_a < end_b and end_a > start_b


def _merge_intervals(intervals):
    if not intervals:
        return []

    sorted_intervals = sorted(intervals, key=lambda item: item[0])
    merged = [list(sorted_intervals[0])]

    for start, end in sorted_intervals[1:]:
        if start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], end)
        else:
            merged.append([start, end])

    return [(start, end) for start, end in merged]


def _busy_intervals_for_date(schedules, reservations, target_date):
    day_of_week = target_date.weekday()
    intervals = []

    for schedule in schedules:
        if schedule.day_of_week != day_of_week:
            continue
        intervals.append(
            (
                _time_to_minutes(schedule.start_time),
                _time_to_minutes(schedule.end_time),
                "class",
                schedule.subject_name,
            )
        )

    for reservation in reservations:
        if reservation.date != target_date:
            continue
        intervals.append(
            (
                _time_to_minutes(reservation.start_time),
                _time_to_minutes(reservation.end_time),
                "reservation",
                None,
            )
        )

    minute_pairs = [(start, end) for start, end, _, _ in intervals]
    merged = _merge_intervals(minute_pairs)

    meta = []
    for start, end in merged:
        related_class = next(
            (
                subject
                for s, e, kind, subject in intervals
                if kind == "class" and s == start and e == end
            ),
            None,
        )
        meta.append((start, end, related_class))

    return meta


def _find_gaps(busy_intervals):
    day_start = _time_to_minutes(STUDY_DAY_START)
    day_end = _time_to_minutes(STUDY_DAY_END)
    cursor = day_start
    gaps = []

    for start, end, _subject in busy_intervals:
        if start > cursor and start - cursor >= MIN_SLOT_MINUTES:
            gaps.append((cursor, start))
        cursor = max(cursor, end)

    if day_end > cursor and day_end - cursor >= MIN_SLOT_MINUTES:
        gaps.append((cursor, day_end))

    return gaps


def _class_before(schedules, day_of_week, slot_start_minutes):
    candidates = [
        schedule
        for schedule in schedules
        if schedule.day_of_week == day_of_week
        and _time_to_minutes(schedule.end_time) <= slot_start_minutes
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda schedule: schedule.end_time)


def _class_after(schedules, day_of_week, slot_end_minutes):
    candidates = [
        schedule
        for schedule in schedules
        if schedule.day_of_week == day_of_week
        and _time_to_minutes(schedule.start_time) >= slot_end_minutes
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda schedule: schedule.start_time)


def _score_slot(slot_start, slot_end, schedules, day_of_week, target_date):
    duration = slot_end - slot_start
    score = duration

    before_class = _class_before(schedules, day_of_week, slot_start)
    after_class_end = _class_before(schedules, day_of_week, slot_start)
    next_class = _class_after(schedules, day_of_week, slot_end)

    tag = "free_time"
    after_subject = None

    if after_class_end and slot_start - _time_to_minutes(after_class_end.end_time) <= 60:
        score += 40
        tag = "after_class"
        after_subject = after_class_end.subject_name
    elif not before_class and slot_start < 11 * 60:
        score += 25
        tag = "morning_prep"
    elif not next_class and slot_end >= 19 * 60:
        score += 20
        tag = "evening_review"
    elif duration >= 120:
        score += 30
        tag = "deep_study"

    today = timezone.localdate()
    if target_date == today:
        score += 10
    elif target_date == today + timedelta(days=1):
        score += 5

    if duration >= 120:
        score += 15

    return score, tag, after_subject


def _slot_title(tag, after_subject):
    if tag == "after_class" and after_subject:
        return f"{after_subject} 수업 직후 복습"
    if tag == "morning_prep":
        return "오전 예습 · 집중 학습"
    if tag == "evening_review":
        return "저녁 정리 · 마무리 학습"
    if tag == "deep_study":
        return "장시간 몰입 학습"
    return "공부하기 좋은 빈 시간"


def find_study_windows(schedules, reservations, today=None):
    today = today or timezone.localdate()
    candidates = []

    for offset in range(LOOKAHEAD_DAYS):
        target_date = today + timedelta(days=offset)
        day_of_week = target_date.weekday()
        busy = _busy_intervals_for_date(schedules, reservations, target_date)

        for gap_start, gap_end in _find_gaps(busy):
            score, tag, after_subject = _score_slot(
                gap_start, gap_end, schedules, day_of_week, target_date
            )
            duration = gap_end - gap_start

            if duration >= 180:
                slot_end = gap_start + 120
            elif duration >= 120:
                slot_end = gap_start + 120
            else:
                slot_end = gap_end

            candidates.append(
                {
                    "date": target_date,
                    "day_label": DAY_LABELS[day_of_week],
                    "start_time": _minutes_to_time(gap_start),
                    "end_time": _minutes_to_time(slot_end),
                    "score": score,
                    "tag": tag,
                    "after_subject": after_subject,
                    "title": _slot_title(tag, after_subject),
                    "duration_minutes": slot_end - gap_start,
                }
            )

    candidates.sort(key=lambda item: (-item["score"], item["date"], item["start_time"]))
    return candidates[:MAX_RECOMMENDATIONS * 2]
