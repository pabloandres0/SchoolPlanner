
import json
import math
from datetime import date, datetime, time, timedelta

import pandas as pd

from estimator import estimate_hours, load_keywords
from paths import BUSY_HOURS_PATH, EVENTS_PATH, PRIORITIES_PATH, SCHEDULE_PATH

SLOT_MINUTES = 30        
STUDY_START_HOUR = 8     
STUDY_END_HOUR = 24      
MAX_HOURS_PER_DAY = 6    
DAYS_AHEAD = 7           

DEFAULT_PRIORITY = 2 
PRIORITY_LABELS = {1: "low", 2: "normal", 3: "high"}

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]
DAY_ALIASES = {
    "mon": 0, "monday": 0, "lun": 0, "lunes": 0,
    "tue": 1, "tuesday": 1, "mar": 1, "martes": 1,
    "wed": 2, "wednesday": 2, "mie": 2, "miercoles": 2, "miércoles": 2,
    "thu": 3, "thursday": 3, "jue": 3, "jueves": 3,
    "fri": 4, "friday": 4, "vie": 4, "viernes": 4,
    "sat": 5, "saturday": 5, "sab": 5, "sábado": 5, "sabado": 5,
    "sun": 6, "sunday": 6, "dom": 6, "domingo": 6,
}


def parse_clock(text):
    parsed = datetime.strptime(text.strip(), "%H:%M")
    return parsed.hour * 60 + parsed.minute


def parse_day(text):
    key = str(text).strip().lower()
    if key not in DAY_ALIASES:
        raise ValueError(f"'{text}' is not a valid day name.")
    return DAY_ALIASES[key]


def parse_due_datetime(value):
    if not value:
        return None
    try:
        if len(value) == 10:  # 'YYYY-MM-DD' (all-day event)
            return datetime.combine(date.fromisoformat(value), time(23, 59))
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return None
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone().replace(tzinfo=None)
    return parsed


def load_events(path=EVENTS_PATH):
    if not path.is_file():
        raise FileNotFoundError(
            "No calendar data yet. Fetch your calendar (or load the sample) first."
        )
    with path.open("r", encoding="utf-8") as events_file:
        return json.load(events_file)


def load_priorities(path=PRIORITIES_PATH):
    if not path.is_file():
        return {}
    with path.open("r", encoding="utf-8") as priorities_file:
        return json.load(priorities_file)


def save_priority(event_id, priority, path=PRIORITIES_PATH):
    priorities = load_priorities(path)
    priorities[event_id] = priority
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as priorities_file:
        json.dump(priorities, priorities_file, indent=4)


def load_busy_hours(path=BUSY_HOURS_PATH):
    busy_blocks = []
    skipped_rows = []
    if not path.is_file():
        return busy_blocks, skipped_rows

    table = pd.read_csv(path, dtype=str).fillna("")
    for row_number, row in table.iterrows():
        try:
            weekday = parse_day(row["day"])
            start = parse_clock(row["start"])
            end = parse_clock(row["end"])
            if end <= start:
                raise ValueError("end must be after start")
            busy_blocks.append((weekday, start, end))
        except (KeyError, ValueError) as error:
            skipped_rows.append(f"row {row_number + 2}: {error}")
    return busy_blocks, skipped_rows


def add_busy_hour(day, start, end, path=BUSY_HOURS_PATH):
    weekday = parse_day(day)
    start_min, end_min = parse_clock(start), parse_clock(end)
    if end_min <= start_min:
        raise ValueError("The end time must be after the start time.")

    new_row = pd.DataFrame([{
        "day": DAY_NAMES[weekday],
        "start": f"{start_min // 60:02d}:{start_min % 60:02d}",
        "end": f"{end_min // 60:02d}:{end_min % 60:02d}",
    }])
    path.parent.mkdir(parents=True, exist_ok=True)
    new_row.to_csv(path, mode="a", header=not path.is_file(), index=False)


def save_schedule(schedule, path=SCHEDULE_PATH):
    path.parent.mkdir(parents=True, exist_ok=True)
    schedule.to_csv(path, index=False)


def load_schedule(path=SCHEDULE_PATH):
    if not path.is_file():
        return pd.DataFrame()
    return pd.read_csv(path)


def get_week_assignments(events, now, keywords, priorities, days_ahead=DAYS_AHEAD):
    """Keep assignments due within the next `days_ahead` days.

    Each returned task is a dict with the estimated hours and priority added.
    Tasks are sorted by due date.
    """
    limit = now + timedelta(days=days_ahead)
    tasks = []
    for event in events:
        due = parse_due_datetime(event.get("fecha_inicio"))
        if due is None or due < now or due > limit:
            continue

        hours, source = estimate_hours(
            event.get("titulo", ""), event.get("descripcion", ""), keywords
        )
        tasks.append({
            "id": event.get("id_evento", ""),
            "title": event.get("titulo", "(untitled)"),
            "course": event.get("materia_codigo", "General"),
            "due": due,
            "hours": hours,
            "source": source,
            "priority": priorities.get(event.get("id_evento", ""), DEFAULT_PRIORITY),
        })
    tasks.sort(key=lambda task: task["due"])
    return tasks


def build_free_slots(now, last_day, busy_blocks):
    """Return {date: [slot_start, ...]} of free 30-minute slots.

    A slot is free when it is in the future and does not overlap any busy
    block on that weekday.
    """
    free_slots = {}
    day = now.date()
    while day <= last_day:
        weekday_busy = [(s, e) for (w, s, e) in busy_blocks if w == day.weekday()]
        day_slots = []
        for start_min in range(STUDY_START_HOUR * 60,
                               STUDY_END_HOUR * 60, SLOT_MINUTES):
            end_min = start_min + SLOT_MINUTES
            slot_start = datetime.combine(day, time(start_min // 60, start_min % 60))
            if slot_start < now:
                continue 
            overlaps = any(start_min < b_end and end_min > b_start
                           for b_start, b_end in weekday_busy)
            if not overlaps:
                day_slots.append(slot_start)
        free_slots[day] = day_slots
        day += timedelta(days=1)
    return free_slots


def merge_slots_into_blocks(assigned):
    assigned.sort(key=lambda item: (item[1], item[0]["id"]))
    blocks = []
    for task, slot_start in assigned:
        slot_end = slot_start + timedelta(minutes=SLOT_MINUTES)
        last = blocks[-1] if blocks else None
        if last and last["task"] is task and last["end"] == slot_start:
            last["end"] = slot_end  # extend the previous block
        else:
            blocks.append({"task": task, "start": slot_start, "end": slot_end})
    return blocks


def build_schedule(tasks, busy_blocks, now):
    warnings = []
    if not tasks:
        return pd.DataFrame(), ["No assignments are due this week."]

    last_day = max(task["due"].date() for task in tasks)
    free_slots = build_free_slots(now, last_day, busy_blocks)
    max_slots_per_day = int(MAX_HOURS_PER_DAY * 60 / SLOT_MINUTES)
    used_slots = {day: 0 for day in free_slots}
    assigned = []  # list of (task, slot_start)

    ordered = sorted(tasks, key=lambda t: (-t["priority"], t["due"]))
    for task in ordered:
        slots_needed = int(task["hours"] * 60 / SLOT_MINUTES)

        usable_days = [d for d in sorted(free_slots) if d <= task["due"].date()]
        def valid_slots(day):
            return [s for s in free_slots[day]
                    if s + timedelta(minutes=SLOT_MINUTES) <= task["due"]]

        days_with_room = [d for d in usable_days
                          if valid_slots(d) and used_slots[d] < max_slots_per_day]
        if not days_with_room:
            warnings.append(f"No free time found for '{task['title']}'.")
            continue

        per_day = math.ceil(slots_needed / len(days_with_room))
        remaining = slots_needed
        for day in days_with_room:
            take = min(per_day, remaining, max_slots_per_day - used_slots[day])
            for slot in valid_slots(day)[:take]:
                assigned.append((task, slot))
                free_slots[day].remove(slot)
                used_slots[day] += 1
                remaining -= 1

        for day in days_with_room:
            if remaining <= 0:
                break
            for slot in valid_slots(day):
                if remaining <= 0 or used_slots[day] >= max_slots_per_day:
                    break
                assigned.append((task, slot))
                free_slots[day].remove(slot)
                used_slots[day] += 1
                remaining -= 1

        if remaining > 0:
            missing = remaining * SLOT_MINUTES / 60
            warnings.append(
                f"Only part of '{task['title']}' fits before its deadline "
                f"({missing:g} h could not be scheduled)."
            )

    rows = []
    for block in merge_slots_into_blocks(assigned):
        task = block["task"]
        hours = (block["end"] - block["start"]).seconds / 3600
        rows.append({
            "date": block["start"].strftime("%Y-%m-%d"),
            "day": DAY_NAMES[block["start"].weekday()],
            "start": block["start"].strftime("%H:%M"),
            "end": block["end"].strftime("%H:%M"),
            "hours": hours,
            "course": task["course"],
            "assignment": task["title"],
            "priority": PRIORITY_LABELS.get(task["priority"], "normal"),
            "due": task["due"].strftime("%a %Y-%m-%d %H:%M"),
        })
    return pd.DataFrame(rows), warnings


def format_schedule(schedule):
    """Return the schedule as printable text, grouped day by day."""
    if schedule.empty:
        return "The schedule is empty."

    lines = []
    for day_date, day_rows in schedule.groupby("date"):
        total = day_rows["hours"].sum()
        lines.append(f"\n{day_rows['day'].iloc[0]} {day_date}  ({total:g} h of homework)")
        lines.append(day_rows[["start", "end", "course", "assignment", "priority"]]
                     .to_string(index=False))
    return "\n".join(lines)
