"""Validate model output against data/schema.json rules (kept torch-free for unit tests)."""
import json

KEYS = {"intent", "date", "time", "place"}
INTENTS = {"alarm_set", "alarm_query", "calendar_set", "calendar_query",
           "calendar_remove", "weather_query", "datetime_query", "recommendation_events"}


def validate(text):
    """Return the parsed dict if text is a valid output, else None."""
    try:
        obj = json.loads(text)
    except (ValueError, TypeError):
        return None
    if not isinstance(obj, dict) or set(obj) != KEYS or obj["intent"] not in INTENTS:
        return None
    if any(not (obj[k] is None or isinstance(obj[k], str)) for k in ("date", "time", "place")):
        return None
    return obj


def extract_json_line(generated):
    """Model continues after 'JSON:'; keep the first non-empty line."""
    for line in generated.strip().splitlines():
        if line.strip():
            return line.strip()
    return ""
