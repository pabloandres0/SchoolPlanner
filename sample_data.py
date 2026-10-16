from datetime import datetime, timedelta, timezone

from icalendar import Calendar, Event

# (title, course, days from now, hour due, description)
SAMPLE_ASSIGNMENTS = [
    ("Reading Response 3", "HIST101", 1, 23,
     "Read chapter 4 and write a short response. Estimated time: 2 hours."),
    ("Calculus Problem Set 5", "MATH201", 2, 23,
     "Complete problems 1-20 from section 3.2."),
    ("Weekly Quiz 4", "CS101", 3, 20,
     "Online quiz covering loops and functions."),
    ("Lab Report 2", "PHYS150", 4, 23,
     "Write up the results of the pendulum experiment."),
    ("Essay: The Industrial Revolution", "HIST101", 5, 23,
     "Argumentative essay, 5 pages."),
    ("Group Project Proposal", "BUS310", 6, 18,
     "Submit a one-page proposal with your team."),
    ("Final Exam Review Sheet", "MATH201", 20, 23,
     "Due far in the future, so the week filter should hide it."),
]


def build_sample_calendar(output_path, now=None):
    now = now or datetime.now()
    calendar = Calendar()
    calendar.add("prodid", "-//SchoolPlanner sample//EN")
    calendar.add("version", "2.0")

    for index, (title, course, days_ahead, hour, description) in enumerate(SAMPLE_ASSIGNMENTS):
        due_local = (now + timedelta(days=days_ahead)).replace(
            hour=hour, minute=59, second=0, microsecond=0
        ).astimezone()
        event = Event()
        event.add("uid", f"sample-{index}@schoolplanner")
        event.add("summary", f"{title} [{course}]")
        event.add("dtstart", due_local.astimezone(timezone.utc))
        event.add("dtend", due_local.astimezone(timezone.utc))
        event.add("description", description)
        event.add("url", f"https://canvas.example.com/assignments/{index}")
        calendar.add_component(event)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(calendar.to_ical())
    return len(SAMPLE_ASSIGNMENTS)
