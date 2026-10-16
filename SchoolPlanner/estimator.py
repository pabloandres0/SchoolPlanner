
import csv
import re

from paths import KEYWORDS_PATH

DEFAULT_HOURS = 1.5       # used when nothing else matches
MIN_HOURS = 0.5           # smallest block we schedule (one 30-minute slot)
MAX_STATED_HOURS = 8      # ignore "24 hours"-style deadlines mentioned in text

# Matches "2 hours", "1.5 hrs", "45 minutes", "3 horas", "20 min" ...
DURATION_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(hours?|hrs?|horas?|minutes?|mins?|minutos?)\b",
    re.IGNORECASE,
)


def load_keywords(path=KEYWORDS_PATH):
    """Read the keyword -> hours table from a CSV file into a dictionary."""
    keywords = {}
    with open(path, "r", encoding="utf-8", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            try:
                keywords[row["keyword"].strip().lower()] = float(row["hours"])
            except (KeyError, ValueError, AttributeError):
                continue  # skip malformed rows instead of crashing
    return keywords


def round_to_half_hour(hours):
    """Round to the nearest 0.5 h, never below MIN_HOURS."""
    rounded = round(hours * 2) / 2
    return max(rounded, MIN_HOURS)


def find_stated_duration(text):
    """Return hours written in the text, or None if there is no usable one."""
    for amount, unit in DURATION_PATTERN.findall(text):
        value = float(amount.replace(",", "."))
        # Minutes -> hours; everything else is already hours.
        hours = value / 60 if unit.lower().startswith(("min", "minuto")) else value
        if 0 < hours <= MAX_STATED_HOURS:
            return hours
    return None


def find_keyword_hours(text, keywords):
    """Return (keyword, hours) for the longest matching keyword, or None."""
    lowered = text.lower()
    best_match = None
    for keyword, hours in keywords.items():
        # \b makes "lab" match "Lab 2" but not "label".
        if re.search(r"\b" + re.escape(keyword) + r"\b", lowered):
            if best_match is None or len(keyword) > len(best_match[0]):
                best_match = (keyword, hours)
    return best_match


def estimate_hours(title, description, keywords):
    """Return (hours, source) where source explains how we got the number."""
    stated = find_stated_duration(title + " " + description)
    if stated is not None:
        return round_to_half_hour(stated), "stated in description"

    # Title is more reliable than the description, so it is checked first.
    for text in (title, description):
        match = find_keyword_hours(text, keywords)
        if match is not None:
            return round_to_half_hour(match[1]), f"keyword '{match[0]}'"

    return DEFAULT_HOURS, "default"
