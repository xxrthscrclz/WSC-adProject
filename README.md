# StudIt — Study It, 공부 환경을 위한 스터디룸 좌석 예약

> **웹서버컴퓨팅 AD 프로젝트**
> 팀명: StudIt | 학번: 20211882 | 이름: 박주호
> **주제:** 수업 시간표 + 좌석 현황 기반 스터디룸 예약 + AI 학습 시간 추천  
> **스택:** Django 6 + SQLite + Bootstrap 5 + Google Gemini API

---

## 1. 프로젝트 개요

**StudIt**(Study It)은 캠퍼스 스터디룸 좌석을 **날짜·시간대** 기준으로 예약하는 풀스택 웹 서비스입니다.  
단순 예약을 넘어, **수업 시간표와의 충돌 검사**, **중복 예약 방지**, **Google Gemini API 기반 AI 학습 시간 추천**을 제공합니다.

### 차별화 포인트

| 항목             | 설명                                                  |
| ---------------- | ----------------------------------------------------- |
| 시간표 연동      | 등록한 수업 시간과 겹치는 예약 자동 차단              |
| 중복 예약 방지   | 동일 좌석·동일 사용자 시간대 중복 예약 불가           |
| AI 학습 추천     | Gemini API로 공백 시간 분석 + 공부 방법 코멘트 생성   |
| 서비스 계층 분리 | `ReservationService`에서 비즈니스 로직·예외 처리      |
| 날짜별 좌석 현황 | 스터디룸 상세·예약 페이지에서 시간대별 예약 현황 확인 |

---

## 2. 구현 기능 목록

| #   | 기능                                                 | 관련 파일                                                   |
| --- | ---------------------------------------------------- | ----------------------------------------------------------- |
| 1   | 회원가입 / 로그인 / 로그아웃 (`django.contrib.auth`) | `accounts/`                                                 |
| 2   | 스터디룸 · 좌석 목록 · 날짜별 현황 조회              | `rooms/`                                                    |
| 3   | 좌석 예약 (날짜·시간 선택, 타임라인 클릭 선택)       | `reservations/views.py`                                     |
| 4   | 시간 중복 예약 방지 (좌석·사용자)                    | `reservations/services.py`                                  |
| 5   | 수업 시간표 등록 · 삭제 · 충돌 검사                  | `timetable/`                                                |
| 6   | 내 예약 목록 · 취소                                  | `reservations/`                                             |
| 7   | 관리자: 스터디룸·좌석·예약·시간표 관리               | `*/admin.py`                                                |
| 8   | **AI 학습 시간 추천** (Google Gemini API)            | `timetable/gemini_client.py`, `timetable/recommendation.py` |

### 주요 URL

| 경로                                       | 설명                             |
| ------------------------------------------ | -------------------------------- |
| `/`                                        | 홈                               |
| `/accounts/signup/`, `/login/`, `/logout/` | 인증                             |
| `/rooms/`                                  | 스터디룸 목록                    |
| `/rooms/<id>/`                             | 스터디룸 상세 (날짜별 좌석 현황) |
| `/reservations/create/<seat_id>/`          | 좌석 예약                        |
| `/reservations/my/`                        | 내 예약 목록                     |
| `/timetable/`                              | 내 수업 시간표                   |
| `/timetable/recommend/`                    | AI 학습 시간 추천                |
| `/admin/`                                  | Django 관리자                    |

---

## 3. 프로젝트 구조

```
AD_Project_StudIt/
├── README.md                 ← 이 파일 (GitHub용 설명)
├── source_code/              ← Django 프로젝트 전체
│   ├── config/               ← 설정, URL, 홈 뷰
│   ├── accounts/             ← 인증
│   ├── rooms/                ← 스터디룸 · 좌석
│   ├── reservations/         ← 예약 + 서비스 계층 + 예외
│   ├── timetable/            ← 시간표 + Gemini AI 추천
│   ├── templates/            ← HTML 템플릿
│   ├── static/               ← CSS, JavaScript
│   ├── .env.example          ← 환경 변수 예시 (API 키는 직접 설정)
│   ├── manage.py
│   └── requirements.txt
├── report/                   ← 프레임워크 비교 리포트 (20211882.pdf)
└── video/                    ← 3분 시연 영상 (20211882.mp4)
```

### 아키텍처 (MVC + Service Layer)

```
[Browser]   → URL (config/urls.py)
            → View (views.py)           ← Request/Response, 폼 처리
            → Service (services.py)     ← 예약·충돌 검사 비즈니스 로직
            → Model (models.py)         ← DB 접근
            → Template                  ← HTML 렌더링
            → External API (Gemini)     ← AI 코멘트 생성
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
- (선택) Google AI Studio API 키 — AI 추천 기능 사용 시

### 설치 및 실행

```bash
cd source_code

# 가상환경 (권장)
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정 (AI 추천 사용 시)
cp .env.example .env
# .env 파일에 GEMINI_API_KEY 입력

# DB 마이그레이션
python manage.py migrate

# 관리자 계정 생성 (스터디룸 등록용)
python manage.py createsuperuser

# 개발 서버 실행
python manage.py runserver
```

브라우저에서 http://127.0.0.1:8000/ 접속

### 환경 변수 (`.env`)

`source_code/.env` 파일을 생성하고 아래 값을 설정합니다.  
`.env`는 Git에 포함되지 않습니다 (`.gitignore` 적용).

```env
GEMINI_API_KEY=your_api_key_here
GEMINI_MODEL=gemini-2.5-flash-lite
```

- API 키 발급: https://aistudio.google.com/app/apikey
- `.env` 수정 후에는 **개발 서버를 재시작**해야 키가 반영됩니다.
- `GEMINI_API_KEY`가 없어도 예약·시간표 기능은 정상 동작합니다. AI 추천은 기본 추천으로 대체됩니다.

### 관리자 페이지

- URL: http://127.0.0.1:8000/admin/
- 스터디룸 · 좌석 · 예약 · 시간표 CRUD

### 시연용 데이터 등록 순서

1. `/admin/` → StudyRoom 추가 (예: "미래관 1F 스터디룸")
2. 같은 화면에서 Seat 인라인 추가 (1번, 2번, …)
3. `/accounts/signup/` → 사용자 가입
4. `/timetable/` → 수업 시간표 등록
5. `/rooms/` → 스터디룸 선택 → 좌석 예약
6. `/timetable/recommend/` → AI 학습 시간 추천 확인
7. `/reservations/my/` → 내 예약 확인

---

## 6. GitHub

> 저장소 URL: https://github.com/xxrthscrclz/AD_Project_STUDIT

```bash
git clone https://github.com/xxrthscrclz/AD_Project_STUDIT.git
cd AD_Project_STUDIT/source_code
pip install -r requirements.txt
cp .env.example .env   # API 키 설정
python manage.py migrate
python manage.py runserver
```

---

## 7. 참고

- Django 공식 문서: https://docs.djangoproject.com/
- Bootstrap 5: https://getbootstrap.com/
- Google Gemini API: https://ai.google.dev/
