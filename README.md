# Campus Seat — 캠퍼스 스터디룸 · 좌석 예약

> **웹서버컴퓨팅 AD 프로젝트** | 학번: 20211882 | 이름: 박주호  
> **주제:** 자율주제 — 수업 시간표 + 실시간 좌석 현황 기반 스터디룸 예약 서비스  
> **스택:** Django 6 + SQLite + Bootstrap 5

---

## 1. 프로젝트 개요

캠퍼스 스터디룸 좌석을 **날짜·시간대** 기준으로 예약하는 웹 서비스입니다.  
기존 단순 예약 시스템과 달리, **수업 시간표와의 충돌 검사**와 **동일 좌석·시간대 중복 예약 방지**를 서비스 계층에서 처리합니다.

### 차별화 포인트

| 항목 | 설명 |
|------|------|
| 시간표 연동 | 사용자가 등록한 수업 시간과 겹치는 예약 차단 |
| 중복 예약 방지 | 같은 좌석·같은 시간대 이중 예약 불가 |
| 서비스 계층 분리 | 비즈니스 로직을 View가 아닌 `ReservationService`에서 처리 |
| 예외 처리 | `TimeOverlapError`, `ScheduleConflictError` 등 커스텀 예외 |

---

## 2. 구현 기능 목록 (7개)

| # | 기능 | 상태 | 관련 파일 |
|---|------|------|-----------|
| 1 | 회원가입 / 로그인 / 로그아웃 | ✅ 기본 구현 | `accounts/` |
| 2 | 스터디룸 · 좌석 목록 조회 | ✅ 기본 구현 | `rooms/` |
| 3 | 좌석 예약 (날짜·시간 선택) | ✅ 기본 구현 | `reservations/views.py` |
| 4 | **시간 중복 예약 방지** | ✅ 서비스 계층 | `reservations/services.py` |
| 5 | **수업 시간표 등록 · 충돌 검사** | ✅ 기본 구현 | `timetable/` |
| 6 | 내 예약 목록 · 취소 | ✅ 기본 구현 | `reservations/` |
| 7 | 관리자: 스터디룸·좌석·예약 관리 | ✅ Django Admin | `*/admin.py` |

### 다음 단계 (UI/UX 보강)

- [ ] 스터디룸 상세 페이지에 **날짜·시간 선택 → 좌석별 실시간 현황** 표시
- [ ] 예약 성공/실패 메시지 (Django messages framework)
- [ ] 시연용 샘플 데이터 로드 커맨드
- [ ] PostgreSQL 전환 (선택)

---

## 3. 프로젝트 구조

```
AD_Project_20211882_박주호/
├── README.md                 ← 이 파일 (GitHub용 설명)
├── source_code/              ← Django 프로젝트
│   ├── config/               ← 설정, URL, 홈 뷰
│   ├── accounts/             ← 인증 (django.contrib.auth)
│   ├── rooms/                ← 스터디룸 · 좌석 모델
│   ├── reservations/         ← 예약 + 서비스 계층 + 예외
│   ├── timetable/            ← 수업 시간표
│   ├── templates/            ← HTML 템플릿
│   ├── static/               ← CSS
│   ├── manage.py
│   └── requirements.txt
├── report/                   ← 프레임워크 비교 리포트 (20211882.pdf)
└── video/                    ← 3분 시연 영상
```

### 아키텍처 (MVC)

```
[Browser] → URL (config/urls.py)
         → View (views.py)        ← 요청/응답, 폼 처리
         → Service (services.py)  ← 비즈니스 로직, 중복·충돌 검사
         → Model (models.py)      ← DB 접근
         → Template               ← HTML 렌더링
```

---

## 4. DB 설계 (ER 개요)

```
User (Django 기본)
 ├── ClassSchedule   (요일, 시작/종료, 과목명, 강의실)
 └── Reservation     (좌석, 날짜, 시작/종료, 상태)

StudyRoom (이름, 건물, 층, 수용 인원)
 └── Seat (좌석 번호)
      └── Reservation
```

### ReservationStatus

- `confirmed` — 확정
- `cancelled` — 취소

---

## 5. 실행 방법

### 사전 요구사항

- Python 3.10+
- pip

### 설치 및 실행

```bash
cd source_code

# 가상환경 (권장)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# DB 마이그레이션
python manage.py migrate

# 관리자 계정 생성 (스터디룸 등록용)
python manage.py createsuperuser

# 개발 서버 실행
python manage.py runserver
```

브라우저에서 http://127.0.0.1:8000/ 접속

### 관리자 페이지

- URL: http://127.0.0.1:8000/admin/
- 스터디룸 · 좌석 · 예약 · 시간표 CRUD

### 시연용 데이터 등록 순서

1. `/admin/` → StudyRoom 추가 (예: "중앙도서관 3F A룸")
2. 같은 화면에서 Seat 인라인 추가 (1번, 2번, …)
3. `/accounts/signup/` → 테스트 사용자 가입
4. `/timetable/` → 수업 시간표 등록
5. `/rooms/` → 스터디룸 선택 → 좌석 예약
6. `/reservations/my/` → 내 예약 확인

---

## 6. 구현 순서 (개발 로드맵)

```
Phase 1 — 프로젝트 생성          ✅ 완료
  ├── Django 프로젝트·앱 구조
  ├── 모델·마이그레이션
  ├── 서비스 계층 (중복·충돌 검사)
  └── 기본 템플릿·URL

Phase 2 — 핵심 기능 마무리       ← 다음
  ├── 좌석 실시간 현황 UI
  ├── Django messages 알림
  └── 샘플 데이터 fixtures

Phase 3 — 제출 준비
  ├── GitHub 저장소 + README
  ├── 3분 시연 영상 촬영
  └── 프레임워크 비교 리포트 (report/20211882.pdf)
```

---

## 7. 3분 시연 영상 구성 (안)

| 시간 | 내용 |
|------|------|
| 0:00~0:30 | 서비스 소개 (문제 → 해결) |
| 0:30~1:00 | 회원가입 · 시간표 등록 |
| 1:00~2:00 | 스터디룸 선택 → 좌석 예약 → 중복/충돌 차단 시연 |
| 2:00~2:30 | 내 예약 목록 · 취소 |
| 2:30~3:00 | 관리자 페이지 · 기술 스택 요약 |

---

## 8. 평가 항목 대응

| 평가 항목 | 대응 내용 |
|-----------|-----------|
| 기능 완성도 | 7개 핵심 기능 (인증, CRUD, 예약, 취소, 시간표, Admin) |
| 주제 독창성 | 시간표 연동 + 중복 예약 방지 |
| 기술 활용 | django.contrib.auth, Request/Response, 서비스 계층, 예외 처리, SQLite |
| UI/UX | Bootstrap 5, 직관적 네비게이션 |
| 코드 구조 | MVC + Service Layer, 앱별 모듈 분리 |

---

## 9. 환경 변수

현재 별도 환경 변수 없음. SQLite 사용.

PostgreSQL 전환 시 `config/settings.py`의 `DATABASES` 설정 변경:

```python
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "campus_seat",
        "USER": "postgres",
        "PASSWORD": "...",
        "HOST": "localhost",
        "PORT": "5432",
    }
}
```

---

## 10. GitHub

> 저장소 URL: _(GitHub 생성 후 여기에 추가)_

```bash
git init
git add .
git commit -m "feat: Campus Seat Django 프로젝트 초기 구현"
git remote add origin <your-repo-url>
git push -u origin main
```

---

## 11. 참고

- Django 공식 문서: https://docs.djangoproject.com/
- Bootstrap 5: https://getbootstrap.com/
