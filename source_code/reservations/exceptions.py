class ReservationError(Exception):
    """예약 관련 비즈니스 예외의 기본 클래스."""


class TimeOverlapError(ReservationError):
    """동일 좌석·시간대에 이미 예약이 존재할 때 발생."""


class ScheduleConflictError(ReservationError):
    """수업 시간표와 예약 시간이 겹칠 때 발생."""


class UserTimeOverlapError(ReservationError):
    """동일 사용자가 같은 시간대에 다른 좌석을 중복 예약하려 할 때 발생."""


class PastReservationError(ReservationError):
    """과거 날짜·시간으로 예약하려 할 때 발생."""
