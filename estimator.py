

import csv
import re

from paths import KEYWORDS_PATH

DEFAULT_HOURS = 1.5      
MIN_HOURS = 0.5           
MAX_STATED_HOURS = 8      

DURATION_PATTERN = re.compile(
    r"(\d+(?:[.,]\d+)?)\s*(hours?|hrs?|horas?|minutes?|mins?|minutos?)\b",
    re.IGNORECASE,
)


def load_keywords(path=KEYWORDS_PATH):
    keywords = {}
    with open(path, "r", encoding="utf-8", newline="") as csv_file:
        for row in csv.DictReader(csv_file):
            try:
                keywords[row["keyword"].strip().lower()] = float(row["hours"])
            except (KeyError, ValueError, AttributeError):
                continue
    return keywords


def round_to_half_hour(hours):
    rounded = round(hours * 2) / 2
    return max(rounded, MIN_HOURS)


def find_stated_duration(text):
    for amount, unit in DURATION_PATTERN.findall(text):
        value = float(amount.replace(",", "."))
        hours = value / 60 if unit.lower().startswith(("min", "minuto")) else value
        if 0 < hours <= MAX_STATED_HOURS:
            return hours
    return None


def find_keyword_hours(text, keywords):
    lowered = text.lower()
    best_match = None
    for keyword, hours in keywords.items():
        if re.search(r"\b" + re.escape(keyword) + r"\b", lowered):
            if best_match is None or len(keyword) > len(best_match[0]):
                best_match = (keyword, hours)
    return best_match


def estimate_hours(title, description, keywords):
    stated = find_stated_duration(title + " " + description)
    if stated is not None:
        return round_to_half_hour(stated), "stated in description"

    for text in (title, description):
        match = find_keyword_hours(text, keywords)
        if match is not None:
            return round_to_half_hour(match[1]), f"keyword '{match[0]}'"

    return DEFAULT_HOURS, "default"
