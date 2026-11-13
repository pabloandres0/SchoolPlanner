#!/usr/bin/env python3
"""
SchoolPlanner Gemini AI Assistant
Provides on-demand duration estimation and step-by-step task breakdown.
Caches results locally in files/ai_estimates.json.
"""

import json
import os
import urllib.request
import urllib.error
from pathlib import Path
from paths import FILES_DIR

AI_CACHE_PATH = FILES_DIR / "ai_estimates.json"
GEMINI_KEYS_PATH = FILES_DIR / "geminikeys.json"

CANDIDATE_MODELS = [
    "gemini-3-flash-preview",
    "gemini-3.8-flash",
    "gemini-flash-latest",
    "gemini-3.1-flash-lite",
]


def load_api_key():
    if not GEMINI_KEYS_PATH.is_file():
        env_key = os.environ.get("GEMINI_API_KEY", "").strip()
        if env_key:
            return env_key
        return None

    try:
        with GEMINI_KEYS_PATH.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("key", "").strip() or None
    except Exception:
        return None


def save_api_key(key):
    """Store the Gemini API key in files/geminikeys.json with 'key' as the only entry."""
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    with GEMINI_KEYS_PATH.open("w", encoding="utf-8") as f:
        json.dump({"key": key.strip()}, f, indent=2)
    return True


def load_ai_cache():
    if not AI_CACHE_PATH.is_file():
        return {}
    try:
        with AI_CACHE_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_ai_cache(cache):
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    with AI_CACHE_PATH.open("w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def round_to_half_hour(hours):
    rounded = round(float(hours) * 2) / 2
    return max(0.5, min(rounded, 8.0))


def analyze_assignment(event_id, title, course, description, force_refresh=False):
    cache = load_ai_cache()
    cache_key = event_id or f"{course}_{title}"

    if not force_refresh and cache_key in cache:
        cached_entry = cache[cache_key]
        return {
            "estimated_hours": cached_entry.get("estimated_hours", 1.5),
            "reasoning": cached_entry.get("reasoning", "Loaded from local AI cache."),
            "subtasks": cached_entry.get("subtasks", []),
            "cached": True,
        }

    api_key = load_api_key()
    if not api_key:
        raise ValueError("No Gemini API key found in files/geminikeys.json or GEMINI_API_KEY environment variable.")

    prompt = f"""You are an expert academic tutor helping a student organize their schedule.
Analyze this course assignment and return a realistic duration estimate and actionable breakdown.

Course: {course}
Assignment Title: {title}
Description & Instructions:
{description if description.strip() else "(No additional description provided)"}

Return ONLY valid JSON matching this structure:
{{
  "estimated_hours": float between 0.5 and 8.0 rounded to nearest 0.5,
  "reasoning": "One concise sentence explaining why this duration was estimated.",
  "subtasks": [
    "Step 1: Concrete action item",
    "Step 2: Concrete action item",
    "Step 3: Concrete action item"
  ]
}}
"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"response_mime_type": "application/json"},
    }
    payload_bytes = json.dumps(payload).encode("utf-8")

    last_error = None
    for model in CANDIDATE_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        req = urllib.request.Request(
            url,
            data=payload_bytes,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=18) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                parsed = json.loads(text)

                hours = round_to_half_hour(parsed.get("estimated_hours", 2.0))
                reasoning = parsed.get("reasoning", "Estimated based on assignment requirements.").strip()
                subtasks = parsed.get("subtasks", [])
                if not isinstance(subtasks, list) or not subtasks:
                    subtasks = [
                        f"Review prompt guidelines for {title}.",
                        "Draft the initial work and core deliverables.",
                        "Perform final check, revisions, and submit.",
                    ]

                result_entry = {
                    "estimated_hours": hours,
                    "reasoning": reasoning,
                    "subtasks": subtasks,
                    "cached": False,
                }

                # Save in cache
                cache[cache_key] = result_entry
                save_ai_cache(cache)
                return result_entry
        except urllib.error.HTTPError as e:
            last_error = f"HTTP {e.code} ({model})"
            continue
        except Exception as e:
            last_error = str(e)
            continue

    raise RuntimeError(f"Gemini API request failed across models: {last_error}")


def apply_ai_estimate(event_id, hours):
    cache = load_ai_cache()
    if event_id in cache:
        cache[event_id]["applied_hours"] = float(hours)
        save_ai_cache(cache)
    return True


def set_manual_hours(event_id, hours):
    """Save a manually entered duration override for an assignment."""
    hours = round_to_half_hour(hours)
    cache = load_ai_cache()
    if event_id in cache:
        cache[event_id]["applied_hours"] = hours
    else:
        cache[event_id] = {"applied_hours": hours}
    save_ai_cache(cache)
    return hours
