#!/usr/bin/env python3
"""
SchoolPlanner Backend Bridge
Provides a JSON interface for the GPUI frontend.
Can be invoked either per-command or run as a persistent JSON-RPC process over stdio.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add current directory to path
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import store_ics
import fetch
import Process
import estimator
import scheduler
import sample_data
import ai_assistant
from paths import (
    CONFIG_PATH,
    ICS_PATH,
    EVENTS_PATH,
    PRIORITIES_PATH,
    BUSY_HOURS_PATH,
    SCHEDULE_PATH,
    EXPORT_PATH,
)
from main import get_week_tasks


def get_status():
    url = ""
    if CONFIG_PATH.is_file():
        try:
            with CONFIG_PATH.open("r", encoding="utf-8") as f:
                data = json.load(f)
                url = data.get("urlFeed", "")
        except Exception:
            pass

    event_count = 0
    if EVENTS_PATH.is_file():
        try:
            with EVENTS_PATH.open("r", encoding="utf-8") as f:
                event_count = len(json.load(f))
        except Exception:
            pass

    busy_blocks, _ = scheduler.load_busy_hours()
    schedule_df = scheduler.load_schedule()
    schedule_count = len(schedule_df) if not schedule_df.empty else 0

    return {
        "url": url,
        "event_count": event_count,
        "busy_count": len(busy_blocks),
        "schedule_count": schedule_count,
        "config_path": str(CONFIG_PATH),
        "export_path": str(EXPORT_PATH),
    }


def validate_url(url: str):
    normalized = store_ics.normalize_url(url.strip())
    if not normalized:
        return {"valid": False, "error": "Empty URL"}
    valid = store_ics.validate_ics_url(normalized)
    return {"valid": valid, "normalized_url": normalized}


def save_and_download(url: str):
    normalized = store_ics.normalize_url(url.strip())
    if not normalized:
        raise ValueError("URL cannot be empty")
    store_ics.save_url(normalized)
    fetch.download_calendar(normalized)
    count = Process.procesar_calendario_canvas(ICS_PATH, EVENTS_PATH)
    return {"count": count, "url": normalized}


def load_sample():
    sample_data.build_sample_calendar(ICS_PATH)
    count = Process.procesar_calendario_canvas(ICS_PATH, EVENTS_PATH)
    return {"count": count}


def list_tasks():
    tasks = get_week_tasks()
    ai_cache = ai_assistant.load_ai_cache()
    output = []
    total_hours = 0.0
    for pos, t in enumerate(tasks):
        hours = float(t["hours"])
        total_hours += hours
        priority_label = scheduler.PRIORITY_LABELS.get(t["priority"], "normal")
        ai_data = ai_cache.get(t["id"])
        output.append({
            "index": pos,
            "id": t["id"],
            "title": t["title"],
            "course": t["course"],
            "due": t["due"].strftime("%a %m-%d %H:%M"),
            "due_iso": t["due"].isoformat(),
            "hours": hours,
            "source": t["source"],
            "priority": t["priority"],
            "priority_label": priority_label.capitalize(),
            "has_ai_plan": ai_data is not None,
            "ai_analysis": ai_data,
        })
    return {"tasks": output, "total_hours": total_hours}


def analyze_assignment(event_id: str, force_refresh: bool = False):
    events = scheduler.load_events()
    target_event = None
    for ev in events:
        if ev.get("id_evento") == event_id:
            target_event = ev
            break
    if not target_event:
        raise ValueError(f"Assignment '{event_id}' not found in saved calendar events.")

    title = target_event.get("titulo", "")
    course = target_event.get("materia_codigo", "General")
    description = target_event.get("descripcion", "")

    return ai_assistant.analyze_assignment(event_id, title, course, description, force_refresh=force_refresh)


def apply_ai_estimate(event_id: str, hours: float):
    ai_assistant.apply_ai_estimate(event_id, float(hours))
    return {"success": True, "event_id": event_id, "hours": float(hours)}


def set_manual_hours(event_id: str, hours: float):
    actual = ai_assistant.set_manual_hours(event_id, float(hours))
    return {"success": True, "event_id": event_id, "hours": actual}


def get_ai_status():
    has_key = ai_assistant.load_api_key() is not None
    cache = ai_assistant.load_ai_cache()
    return {"configured": has_key, "cached_count": len(cache)}


def set_priority(event_id: str, priority: int):
    if priority not in (1, 2, 3):
        raise ValueError("Priority must be 1 (low), 2 (normal), or 3 (high)")
    scheduler.save_priority(event_id, priority)
    return {"success": True, "event_id": event_id, "priority": priority}


def list_busy_hours():
    blocks, skipped = scheduler.load_busy_hours()
    formatted = []
    for pos, (weekday, start, end) in enumerate(blocks):
        start_str = f"{start // 60:02d}:{start % 60:02d}"
        end_str = f"{end // 60:02d}:{end % 60:02d}"
        formatted.append({
            "index": pos,
            "weekday": weekday,
            "day": scheduler.DAY_NAMES[weekday],
            "start": start_str,
            "end": end_str,
            "start_minutes": start,
            "end_minutes": end,
        })
    return {"blocks": formatted, "skipped": skipped}


def add_busy_hour(day: str, start: str, end: str):
    scheduler.add_busy_hour(day, start, end)
    return {"success": True}


def delete_busy_hour(index: int):
    scheduler.delete_busy_hour(index)
    return {"success": True}


def generate_schedule():
    tasks = get_week_tasks()
    busy_blocks, skipped_rows = scheduler.load_busy_hours()

    schedule, warnings = scheduler.build_schedule(tasks, busy_blocks, datetime.now())
    notes = list(warnings)
    notes += [f"Ignored busy-hour {msg}" for msg in skipped_rows]
    if not busy_blocks:
        notes.append("No busy hours saved: all hours count as free.")

    if schedule.empty:
        scheduler.clear_schedule()
        notes.append("No study blocks to schedule or existing schedule cleared.")
        return {
            "blocks": [],
            "days": [],
            "total_blocks": 0,
            "total_hours": 0.0,
            "notes": notes,
        }

    scheduler.save_schedule(schedule)

    days_grouped = []
    blocks = []
    for date_text, day_rows in schedule.groupby("date"):
        day_total = float(day_rows["hours"].sum())
        day_name = str(day_rows["day"].iloc[0])
        day_blocks = []
        for _, row in day_rows.iterrows():
            block_data = {
                "date": date_text,
                "day": day_name,
                "start": str(row["start"]),
                "end": str(row["end"]),
                "hours": float(row["hours"]),
                "course": str(row["course"]),
                "assignment": str(row["assignment"]),
                "priority": str(row["priority"]).capitalize(),
                "due": str(row.get("due", "")),
            }
            day_blocks.append(block_data)
            blocks.append(block_data)

        days_grouped.append({
            "date": date_text,
            "day": day_name,
            "total_hours": day_total,
            "blocks": day_blocks,
        })

    return {
        "blocks": blocks,
        "days": days_grouped,
        "total_blocks": len(schedule),
        "total_hours": float(schedule["hours"].sum()),
        "notes": notes,
    }


def get_schedule():
    schedule = scheduler.load_schedule()
    if schedule.empty:
        return {
            "blocks": [],
            "days": [],
            "total_blocks": 0,
            "total_hours": 0.0,
        }

    days_grouped = []
    blocks = []
    for date_text, day_rows in schedule.groupby("date"):
        day_total = float(day_rows["hours"].sum())
        day_name = str(day_rows["day"].iloc[0])
        day_blocks = []
        for _, row in day_rows.iterrows():
            block_data = {
                "date": date_text,
                "day": day_name,
                "start": str(row["start"]),
                "end": str(row["end"]),
                "hours": float(row["hours"]),
                "course": str(row["course"]),
                "assignment": str(row["assignment"]),
                "priority": str(row["priority"]).capitalize(),
                "due": str(row.get("due", "")),
            }
            day_blocks.append(block_data)
            blocks.append(block_data)

        days_grouped.append({
            "date": date_text,
            "day": day_name,
            "total_hours": day_total,
            "blocks": day_blocks,
        })

    return {
        "blocks": blocks,
        "days": days_grouped,
        "total_blocks": len(schedule),
        "total_hours": float(schedule["hours"].sum()),
    }


def export_schedule():
    schedule = scheduler.load_schedule()
    if schedule.empty:
        raise ValueError("No schedule available to export. Generate one first.")
    count = scheduler.export_schedule_ics(schedule)
    return {"count": count, "path": str(EXPORT_PATH)}


DISPATCH = {
    "get_status": lambda args: get_status(),
    "validate_url": lambda args: validate_url(args.get("url", "")),
    "save_and_download": lambda args: save_and_download(args.get("url", "")),
    "load_sample": lambda args: load_sample(),
    "list_tasks": lambda args: list_tasks(),
    "set_priority": lambda args: set_priority(args["event_id"], int(args["priority"])),
    "list_busy_hours": lambda args: list_busy_hours(),
    "add_busy_hour": lambda args: add_busy_hour(args["day"], args["start"], args["end"]),
    "delete_busy_hour": lambda args: delete_busy_hour(int(args["index"])),
    "generate_schedule": lambda args: generate_schedule(),
    "get_schedule": lambda args: get_schedule(),
    "export_schedule": lambda args: export_schedule(),
    "analyze_assignment": lambda args: analyze_assignment(args["event_id"], args.get("force_refresh", False)),
    "apply_ai_estimate": lambda args: apply_ai_estimate(args["event_id"], float(args["hours"])),
    "set_manual_hours": lambda args: set_manual_hours(args["event_id"], float(args["hours"])),
    "get_ai_status": lambda args: get_ai_status(),
}


def handle_request(req):
    action = req.get("action")
    args = req.get("args", {})
    if action not in DISPATCH:
        return {"status": "error", "message": f"Unknown action: {action}"}
    try:
        result = DISPATCH[action](args)
        return {"status": "ok", "data": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}


def run_server():
    """Persistent stdio line protocol"""
    sys.stdout.write(json.dumps({"status": "ready"}) + "\n")
    sys.stdout.flush()

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
            res = handle_request(req)
        except Exception as e:
            res = {"status": "error", "message": f"Malformed request: {e}"}
        sys.stdout.write(json.dumps(res) + "\n")
        sys.stdout.flush()


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        run_server()
        return

    if len(sys.argv) > 1:
        action = sys.argv[1]
        args = {}
        if len(sys.argv) > 2:
            try:
                args = json.loads(sys.argv[2])
            except Exception:
                args = {"arg": sys.argv[2]}
        res = handle_request({"action": action, "args": args})
        print(json.dumps(res))
        return

    # Default action
    print(json.dumps(handle_request({"action": "get_status"})))


if __name__ == "__main__":
    main()
