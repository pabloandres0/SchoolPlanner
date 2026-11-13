import json
from datetime import datetime
from urllib.error import URLError

import pandas as pd

import ai_assistant
import scheduler
import store_ics
from estimator import load_keywords
from fetch import fetch_calendar, use_sample_calendar
from paths import BUSY_HOURS_PATH, SCHEDULE_PATH, EXPORT_PATH

EXPECTED_ERRORS = (FileNotFoundError, json.JSONDecodeError, OSError, URLError, ValueError, RuntimeError)


def ask_number(prompt, low, high):
    while True:
        answer = input(prompt).strip()
        if answer.isdigit() and low <= int(answer) <= high:
            return int(answer)
        print(f"Please enter a number from {low} to {high}.")


def ask_yes_no(prompt):
    while True:
        answer = input(prompt + " (y/n): ").strip().lower()
        if answer in ("y", "yes", "s", "si", "sí"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please answer y or n.")


def get_week_tasks():
    events = scheduler.load_events()
    keywords = load_keywords()
    priorities = scheduler.load_priorities()
    return scheduler.get_week_assignments(events, datetime.now(), keywords, priorities)


def show_assignments():
    tasks = get_week_tasks()
    if not tasks:
        print("No assignments are due in the next 7 days.")
        return

    ai_cache = ai_assistant.load_ai_cache()

    table = pd.DataFrame([{
        "#": number,
        "due": task["due"].strftime("%a %m-%d %H:%M"),
        "course": task["course"],
        "assignment": task["title"],
        "est. hours": task["hours"],
        "estimated from": task["source"],
        "priority": scheduler.PRIORITY_LABELS.get(task["priority"], "normal"),
        "AI plan": "Ready" if task["id"] in ai_cache else "-",
    } for number, task in enumerate(tasks, start=1)])

    print("\nAssignments due in the next 7 days:\n")
    print(table.to_string(index=False))
    print(f"\nTotal estimated work: {table['est. hours'].sum():g} hours")


def set_priority():
    tasks = get_week_tasks()
    if not tasks:
        print("No assignments are due in the next 7 days.")
        return

    for number, task in enumerate(tasks, start=1):
        label = scheduler.PRIORITY_LABELS.get(task["priority"], "normal")
        print(f"{number}. {task['title']} [{task['course']}] - priority: {label}")

    chosen = ask_number("Which assignment? ", 1, len(tasks))
    priority = ask_number("Priority (1 = low, 2 = normal, 3 = high): ", 1, 3)

    scheduler.save_priority(tasks[chosen - 1]["id"], priority)
    print(f"Saved. '{tasks[chosen - 1]['title']}' is now "
          f"{scheduler.PRIORITY_LABELS[priority]} priority.")


def ai_assignment_plan():
    tasks = get_week_tasks()
    if not tasks:
        print("No assignments are due in the next 7 days.")
        return

    ai_cache = ai_assistant.load_ai_cache()
    has_key = ai_assistant.load_api_key() is not None

    print("\nAssignments due in the next 7 days:")
    for number, task in enumerate(tasks, start=1):
        task_id = task["id"]
        cached = ai_cache.get(task_id)
        if cached:
            plan_tag = f"[Plan Ready: {cached.get('estimated_hours', task['hours']):.1f}h]"
        else:
            plan_tag = "[No AI Plan]"
        print(f"{number}. {task['title']} [{task['course']}] - est: {task['hours']}h ({task['source']}) {plan_tag}")

    chosen = ask_number(f"\nWhich assignment would you like to plan with Gemini AI? (1-{len(tasks)}, 0 to return): ", 0, len(tasks))
    if chosen == 0:
        return

    selected_task = tasks[chosen - 1]
    task_id = selected_task["id"]
    cached_entry = ai_cache.get(task_id)

    force_refresh = False
    if cached_entry:
        print(f"\nAn AI plan already exists for '{selected_task['title']}'.")
        print("1. View existing AI plan & workload")
        print("2. Re-analyze with Gemini AI (refresh)")
        print("3. Return to main menu")
        action = ask_number("Choose an option: ", 1, 3)
        if action == 3:
            return
        if action == 2:
            force_refresh = True

    if force_refresh or not cached_entry:
        if not has_key:
            print("\nError: No Gemini API key found.")
            print("Please add your Google AI Studio API key to files/geminikeys.json or set the GEMINI_API_KEY environment variable.")
            return

        events = scheduler.load_events()
        target_event = next((ev for ev in events if ev.get("id_evento") == task_id), None)
        description = target_event.get("descripcion", "") if target_event else ""
        print(f"\nAnalyzing instructions for '{selected_task['title']}' with Gemini AI...")
        try:
            analysis = ai_assistant.analyze_assignment(
                task_id,
                selected_task["title"],
                selected_task["course"],
                description,
                force_refresh=True,
            )
        except Exception as err:
            print(f"\nCould not generate AI plan: {err}")
            return
    else:
        analysis = cached_entry

    hours = analysis.get("estimated_hours", selected_task["hours"])
    reasoning = analysis.get("reasoning", "No rationale provided.")
    subtasks = analysis.get("subtasks", [])

    print("\n" + "=" * 65)
    print(f"✦ Gemini AI Workload & Action Plan: {selected_task['title']}")
    print(f"Course: {selected_task['course']} | Due: {selected_task['due'].strftime('%a %m-%d %H:%M')}")
    print("=" * 65)
    print(f"Suggested Workload: {hours:.1f} hours")
    print(f"Rationale: {reasoning}")
    print("\nAction Plan Checklist:")
    if subtasks:
        for idx, step in enumerate(subtasks, start=1):
            print(f"  [{idx}] {step}")
    else:
        print("  (No subtasks listed)")
    print("=" * 65)

    if ask_yes_no(f"\nApply {hours:.1f} hours to this assignment's schedule?"):
        ai_assistant.apply_ai_estimate(task_id, hours)
        print(f"Saved! '{selected_task['title']}' is now set to {hours:.1f} hours (Source: Gemini AI).")
        print("Tip: Select 'Generate my homework schedule' to update your schedule.")


def add_busy_hours():
    print(f"\nBusy hours are saved in: {BUSY_HOURS_PATH}")
    print("Example: day = Monday, start = 08:00, end = 13:30")

    while True:
        day = input("Day (e.g. Monday): ")
        start = input("Start time (HH:MM, 24-hour): ")
        end = input("End time (HH:MM, 24-hour): ")
        try:
            scheduler.add_busy_hour(day, start, end)
            print("Busy block saved.")
        except ValueError as error:
            print(f"Could not save that block: {error}")

        if not ask_yes_no("Add another busy block?"):
            break


def generate_schedule():
    tasks = get_week_tasks()
    busy_blocks, skipped_rows = scheduler.load_busy_hours()

    if skipped_rows:
        print("Some busy-hour rows were ignored:")
        for message in skipped_rows:
            print("  -", message)
    if not busy_blocks:
        print("Note: no busy hours saved, so every hour counts as free (option 7 adds them).")

    schedule, warnings = scheduler.build_schedule(tasks, busy_blocks, datetime.now())
    for message in warnings:
        print("Warning:", message)

    if schedule.empty:
        scheduler.clear_schedule()
        print("The previously saved schedule was cleared because it no longer applies.")
        return

    scheduler.save_schedule(schedule)
    print(scheduler.format_schedule(schedule))
    print(f"\nSchedule saved to: {SCHEDULE_PATH}")


def view_schedule():
    schedule = scheduler.load_schedule()
    if schedule.empty:
        print("No saved schedule yet. Choose 'Generate schedule' first.")
        return
    print(scheduler.format_schedule(schedule))


def export_schedule():
    schedule = scheduler.load_schedule()
    if schedule.empty:
        print("No saved schedule yet. Choose 'Generate schedule' first.")
        return
    count = scheduler.export_schedule_ics(schedule)
    print(f"{count} study blocks exported to: {EXPORT_PATH}")
    print("In Google Calendar: Settings > Import & export > Import, then pick that file.")


MENU = {
    1: ("Set up Canvas calendar URL", store_ics.setup_url),
    2: ("Download my Canvas calendar", fetch_calendar),
    3: ("Load SAMPLE calendar (demo, no Canvas needed)", use_sample_calendar),
    4: ("Show this week's assignments", show_assignments),
    5: ("Set assignment priority", set_priority),
    6: ("AI assignment plan & workload estimate (Gemini)", ai_assignment_plan),
    7: ("Add busy hours (classes, work...)", add_busy_hours),
    8: ("Generate my homework schedule", generate_schedule),
    9: ("View saved schedule", view_schedule),
    10: ("Export schedule to .ics file", export_schedule),
}
EXIT_OPTION = len(MENU) + 1


def print_menu():
    """Display the numbered options."""
    print("\n===== SchoolPlanner =====")
    for number, (text, _) in MENU.items():
        print(f"{number}. {text}")
    print(f"{EXIT_OPTION}. Exit")


def main():
    while True:
        print_menu()
        choice = ask_number("Choose an option: ", 1, EXIT_OPTION)

        if choice == EXIT_OPTION:
            print("Goodbye! Good luck with your homework.")
            break

        _, action = MENU[choice]
        try:
            action()
        except EXPECTED_ERRORS as error:
            print(f"\nSomething went wrong: {error}")


if __name__ == "__main__":
    main()
