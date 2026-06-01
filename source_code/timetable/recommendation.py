from datetime import timedelta

from django.utils import timezone

from reservations.models import Reservation, ReservationStatus
from reservations.services import ReservationService
from rooms.models import Seat

from .models import ClassSchedule
from .gemini_client import GeminiError, generate_study_commentary, is_gemini_configured
from .slots import find_study_windows


STUDY_METHODS = {
    "after_class": "수업 직후 10분 안에 핵심 개념 3가지를 적고, 25분 포모도로로 예제 문제를 풀어 보세요.",
    "morning_prep": "오늘 배울 내용을 미리 훑은 뒤, 질문 2~3개를 메모해 수업에서 확인하세요.",
    "evening_review": "오늘 배운 내용을 한 장 요약 노트로 정리하고, 모르는 부분만 표시해 다음 날 복습하세요.",
    "deep_study": "90분 집중 + 15분 휴식으로 나누고, 중간중간 스스로에게 설명하듯 말로 복습하세요.",
    "free_time": "목표를 하나 정한 뒤 타이머를 켜고, 끝나면 5분간 배운 내용을 소리 내어 정리하세요.",
}

FALLBACK_COMMENTS = {
    "after_class": "{subject} 수업 내용이 아직 생생할 때 복습하면 기억 정착에 가장 효과적입니다.",
    "morning_prep": "수업 전 오전 시간은 집중력이 높아 예습과 개념 정리에 적합합니다.",
    "evening_review": "하루 수업을 마친 뒤 저녁 시간에 정리하면 장기 기억으로 전환하기 좋습니다.",
    "deep_study": "수업 사이 긴 공백은 과제와 심화 학습을 위한 몰입 시간으로 활용하기 좋습니다.",
    "free_time": "수업과 예약 사이의 빈 시간을 활용하면 학습 루틴을 꾸준히 유지할 수 있습니다.",
}


def _format_schedule_summary(schedules):
    if not schedules:
        return "등록된 수업 없음 (자유 시간 위주로 추천)"

    lines = []
    for schedule in schedules:
        day = schedule.get_day_of_week_display()
        lines.append(
            f"- {day} {schedule.start_time.strftime('%H:%M')}~{schedule.end_time.strftime('%H:%M')} "
            f"{schedule.subject_name}"
        )
    return "\n".join(lines)


def _find_available_seat(reservation_date, start_time, end_time):
    overlapping = ReservationService._overlapping_reservations(
        reservation_date, start_time, end_time
    )
    reserved_seat_ids = set(overlapping.values_list("seat_id", flat=True))

    return (
        Seat.objects.filter(is_active=True, room__is_active=True)
        .exclude(id__in=reserved_seat_ids)
        .select_related("room")
        .order_by("room__building", "room__floor", "seat_number")
        .first()
    )


def _fallback_comment(slot):
    template = FALLBACK_COMMENTS.get(slot["tag"], FALLBACK_COMMENTS["free_time"])
    subject = slot.get("after_subject") or "직전 수업"
    return template.format(subject=subject)


def _fallback_summary(schedules, slots):
    if not schedules:
        return (
            "등록된 수업 시간표가 없어 일반적인 학습 시간대를 추천했습니다. "
            "시간표를 등록하면 수업과 겹치지 않는 맞춤 추천을 받을 수 있습니다."
        )
    if not slots:
        return "앞으로 일주일간 여유로운 학습 시간을 찾기 어렵습니다. 예약을 조정하거나 시간표를 확인해 주세요."
    return (
        f"수업 {len(schedules)}개를 분석해 공백 시간 {len(slots)}곳을 골랐습니다. "
        "수업 직후·오전·저녁 시간대는 기억 정착과 복습에 특히 효과적입니다."
    )


def _fallback_study_tips(schedules):
    if not schedules:
        return (
            "하루 2~3시간 단위로 목표를 나누고, 스터디룸 예약 후 바로 시작하세요. "
            "짧은 세션도 타이머와 요약 노트를 함께 쓰면 효율이 올라갑니다."
        )
    return (
        "수업 직후 1~2시간은 복습 골든타임입니다. "
        "긴 공백은 심화 학습, 저녁은 하루 정리에 쓰고, "
        "포모도로(25분 집중 + 5분 휴식)와 액티브 리콜을 병행해 보세요."
    )


def _apply_llm_commentary(slots, llm_data):
    slot_comments = {item.get("index"): item for item in llm_data.get("slots", [])}

    for index, slot in enumerate(slots):
        llm_slot = slot_comments.get(index, {})
        slot["comment"] = llm_slot.get("comment") or _fallback_comment(slot)
        slot["study_method"] = llm_slot.get("study_method") or STUDY_METHODS.get(
            slot["tag"], STUDY_METHODS["free_time"]
        )

    from django.conf import settings

    return {
        "summary": llm_data.get("summary") or _fallback_summary([], slots),
        "study_tips": llm_data.get("study_tips") or _fallback_study_tips([]),
        "slots": slots,
        "llm_used": True,
        "llm_status": f"Google Gemini ({settings.GEMINI_MODEL}) 연결 성공!",
    }


def _build_base_result(schedules, slots, schedule_summary, grid):
    return {
        "schedule_summary": schedule_summary,
        "grid": grid,
        "has_schedules": bool(schedules),
        "gemini_configured": is_gemini_configured(),
    }


def generate_recommendations(user):
    schedules = list(ClassSchedule.objects.filter(user=user))
    today = timezone.localdate()
    reservations = list(
        Reservation.objects.filter(
            user=user,
            date__gte=today,
            date__lte=today + timedelta(days=7),
            status=ReservationStatus.CONFIRMED,
        )
    )

    raw_windows = find_study_windows(schedules, reservations, today=today)
    slots = []

    for window in raw_windows:
        seat = _find_available_seat(
            window["date"], window["start_time"], window["end_time"]
        )
        if not seat:
            continue

        slots.append(
            {
                **window,
                "date_str": window["date"].isoformat(),
                "start_str": window["start_time"].strftime("%H:%M"),
                "end_str": window["end_time"].strftime("%H:%M"),
                "seat": seat,
                "seat_id": seat.id,
                "room_name": str(seat.room),
                "comment": _fallback_comment(window),
                "study_method": STUDY_METHODS.get(
                    window["tag"], STUDY_METHODS["free_time"]
                ),
            }
        )
        if len(slots) >= 5:
            break

    schedule_summary = _format_schedule_summary(schedules)
    grid = _build_schedule_context(schedules)

    if not slots:
        return {
            "summary": _fallback_summary(schedules, slots),
            "study_tips": _fallback_study_tips(schedules),
            "slots": [],
            "llm_used": False,
            "llm_status": "추천 가능한 시간대가 없습니다.",
            **_build_base_result(schedules, slots, schedule_summary, grid),
        }

    llm_payload = [
        {
            "index": index,
            "day": slot["day_label"],
            "date": slot["date_str"],
            "time": f"{slot['start_str']}~{slot['end_str']}",
            "title": slot["title"],
            "tag": slot["tag"],
            "after_subject": slot.get("after_subject"),
        }
        for index, slot in enumerate(slots)
    ]

    if is_gemini_configured():
        try:
            llm_data = generate_study_commentary(schedule_summary, llm_payload)
            result = _apply_llm_commentary(slots, llm_data)
            result.update(_build_base_result(schedules, slots, schedule_summary, grid))
            return result
        except GeminiError:
            pass

    return {
        "summary": _fallback_summary(schedules, slots),
        "study_tips": _fallback_study_tips(schedules),
        "slots": slots,
        "llm_used": False,
        "llm_status": (
            "Gemini API 연결 실패 — 시간표 기반 추천을 사용했습니다. "
            "`.env`의 GEMINI_API_KEY를 확인해 주세요."
            if is_gemini_configured()
            else "`.env`에 GEMINI_API_KEY를 설정하면 Gemini AI 코멘트를 받을 수 있습니다."
        ),
        **_build_base_result(schedules, slots, schedule_summary, grid),
    }


def _build_schedule_context(schedules):
    from .grid import build_weekly_grid

    return build_weekly_grid(schedules, force_start=8, force_end=23)
