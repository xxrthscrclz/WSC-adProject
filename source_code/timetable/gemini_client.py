import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request

from django.conf import settings

from .llm_prompts import build_study_commentary_prompt

try:
    import certifi

    SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
except ImportError:
    SSL_CONTEXT = ssl.create_default_context()

RETRYABLE_STATUS_CODES = {429, 503, 500}


class GeminiError(Exception):
    pass


def is_gemini_configured():
    return bool(settings.GEMINI_API_KEY)


def _model_candidates():
    primary = settings.GEMINI_MODEL
    fallbacks = ["gemini-2.5-flash-lite", "gemini-flash-latest", "gemini-2.5-flash"]
    models = [primary]
    for model in fallbacks:
        if model not in models:
            models.append(model)
    return models


def _parse_json_response(raw_text):
    text = raw_text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise GeminiError("Gemini JSON 응답을 해석할 수 없습니다.") from exc


def _call_gemini(prompt, model):
    query = urllib.parse.urlencode({"key": settings.GEMINI_API_KEY})
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model}:generateContent?{query}"
    )

    payload = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "temperature": 0.7,
                "responseMimeType": "application/json",
            },
        }
    ).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(
        request, timeout=settings.GEMINI_TIMEOUT, context=SSL_CONTEXT
    ) as response:
        body = json.loads(response.read().decode("utf-8"))

    candidates = body.get("candidates") or []
    if not candidates:
        raise GeminiError("Gemini 응답이 비어 있습니다.")

    parts = candidates[0].get("content", {}).get("parts") or []
    if not parts:
        raise GeminiError("Gemini 응답 본문이 비어 있습니다.")

    raw = parts[0].get("text", "").strip()
    if not raw:
        raise GeminiError("Gemini 응답 텍스트가 비어 있습니다.")

    return _parse_json_response(raw)


def generate_study_commentary(schedule_summary, slot_payloads):
    if not is_gemini_configured():
        raise GeminiError("GEMINI_API_KEY가 설정되지 않았습니다.")

    prompt = build_study_commentary_prompt(schedule_summary, slot_payloads)
    last_error = None

    for model in _model_candidates():
        try:
            return _call_gemini(prompt, model)
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            last_error = GeminiError(f"Gemini API 오류 ({exc.code}): {detail[:200]}")
            if exc.code in RETRYABLE_STATUS_CODES:
                continue
            raise last_error from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise GeminiError("Gemini API에 연결할 수 없습니다.") from exc
        except GeminiError as exc:
            last_error = exc
            continue

    if last_error:
        raise last_error
    raise GeminiError("Gemini API 호출에 실패했습니다.")
