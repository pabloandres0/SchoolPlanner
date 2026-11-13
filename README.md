# SchoolPlanner

### Plan your days, weeks, even your month!

## About the Project

SchoolPlanner is a smart Canvas homework and task planner. It reads your Canvas calendar, finds the assignments due in the next 7 days, estimates how long each one will take, and builds an optimal hour-by-hour study schedule around the times you are already busy.

The program supports both **rule-based** estimation—checking for a stated duration in the assignment description (for example, `"Estimated time: 2 hours"`) or matching keywords in the title such as `"quiz"`, `"essay"`, or `"lab"`. Additionally, there's support for **AI-powered** estimation via Gemini, which can also generate a step-by-step plan. Tasks are prioritized based on user-defined importance, estimated work time, and proximity to due dates so you can focus on what matters most.

You can use SchoolPlanner from a graphical window (`gui.py`) or from a text menu (`main.py`). Both use the same underlying code and saved local data.

## Getting Started & Installation

Before doing anything else, clone the GitHub repository to your computer.

**Requirements:**
- **Python 3.10 or newer.** Tkinter (used by the graphical interface) comes bundled with the official installers from python.org for Windows and macOS. *(On macOS with Homebrew Python, run `brew install python-tk` once.)*
- **Gemini API Key (optional, for AI features):** Obtain a free or paid API key from [Google AI Studio](https://aistudio.google.com/u/0/api-keys).

### 1. Open Your Terminal or Command Prompt

- **Windows:** Press the **Windows Key**, type `cmd`, and open **Command Prompt**.
- **macOS:** Press **Command + Space** to open Spotlight, type `Terminal`, and press **Enter**.

### 2. Navigate to the Project Directory

Locate the `SchoolPlanner` folder on your computer and run the command corresponding to your operating system:

- **Windows (Command Prompt):**
  ```cmd
  cd C:\Users\"your name"\Downloads\SchoolPlanner
  ```
- **macOS (Terminal):**
  ```bash
  cd ~/Downloads/SchoolPlanner
  ```

You can also type `cd` followed by a space and drag the `SchoolPlanner` folder directly into the terminal/CMD window.

### 3. Install Required Dependencies

In the same terminal window, run the installation command:

- **Windows:**
  ```cmd
  pip install -r requirements.txt
  ```
- **macOS:**
  ```bash
  pip3 install -r requirements.txt
  ```

## Running the Program

Once the installation is complete, launch the application from the same terminal window.

**Graphical interface (recommended):**

- **Windows:**
  ```cmd
  python gui.py
  ```
- **macOS:**
  ```bash
  python3 gui.py
  ```

**Text menu:**

- **Windows:**
  ```cmd
  python main.py
  ```
- **macOS:**
  ```bash
  python3 main.py
  ```

### Setting Up Your Gemini API Key (For AI Estimation)

1. Visit Google AI Studio's [API panel](https://aistudio.google.com/u/0/api-keys).
2. Click **Create API key** and follow the prompts.
3. Copy the generated API key.
4. Open SchoolPlanner and paste the API key into the designated input box.

### Quick Tour (No Canvas Account Needed)

1. In the **1. Calendar** tab, click **Load sample calendar (demo)**.
2. In **2. Assignments**, select a task and set its priority.
3. In **3. Busy hours**, add the times you cannot study (for example, Monday `08:00` to `14:00`).
4. In **4. Schedule**, click **Generate schedule**, then **Export to Google Calendar (.ics)**.

To use your real calendar, open Canvas, go to **Calendar > Calendar Feed**, copy the link, and paste it in the **1. Calendar** tab. The link is private and stored only locally on your computer (inside the `files/` folder, which is ignored by Git).

## Implemented Features

- **Canvas Integration:** Validate and save your Canvas calendar link (`webcal://` links are accepted), download assignments, clean event data, and filter tasks due within the next 7 days.
- **Flexible Time Estimation:** Estimate completion hours from stated durations, bilingual keywords (English and Spanish), or using Gemini AI (which also generates a step-by-step plan).
- **Task Prioritization:** Assign priority levels (`low`, `normal`, `high`) and automatically prioritize nearest deadlines.
- **Custom Busy Hours:** Save, add, and delete recurring weekly busy blocks.
- **Smart Block Scheduling:** Generate an hour-by-hour schedule in 30-minute blocks from `08:00` to midnight, capped at a maximum of 6 hours of homework per day.
- **Calendar Export & Persistence:** Export schedules to `.ics` files compatible with Google Calendar, Apple Calendar, and Outlook, with all settings and data saved locally between sessions.
- **Dual Interfaces & Demo Mode:** Choose between a four-tab Tkinter GUI or a CLI text menu, plus a built-in sample calendar for testing without a Canvas account.

## How the Schedule is Built

1. Each assignment's workload is distributed across the days between today and its due date so tasks are not left for the last night.
2. High-priority assignments claim time slots first. For equal priorities, the earliest due date goes first.
3. Blocks are never scheduled during your busy hours, in the past, or after an assignment's deadline.
4. If an assignment cannot fit before its deadline, the program displays a warning indicating the unscheduled hours.
5. If no tasks remain to be scheduled, any previously saved schedule is cleared so outdated plans are never shown or exported.

## Technical Decisions

- **Lightweight Dependencies:** `pandas` handles CSV operations and schedule table formatting, while `icalendar` parses the Canvas feed and exports `.ics` files. Everything else (`tkinter`, `json`, `csv`, `re`, `datetime`, `urllib`, `threading`) relies on the Python standard library.
- **Responsive Tkinter UI:** Built with Python's native GUI toolkit for cross-platform compatibility without heavy external dependencies. Network downloads run in background threads so the interface never freezes.
- **Modular Architecture:** The GUI (`gui.py`) and text menu (`main.py`) contain no scheduling logic; both call shared functions across `scheduler.py`, `estimator.py`, `store_ics.py`, and `fetch.py` for clean separation of concerns.
- **Plain-Text Local Persistence:** JSON stores settings, calendar events, and priorities, while CSV stores busy hours and generated schedules—making data transparent and easy to inspect or edit manually.
- **Editable Estimation Rules:** The keyword-to-hours mapping lives in `data/duration_keywords.csv`, allowing new keywords and durations to be added without modifying source code.
- **Time Zone Handling:** Canvas UTC timestamps are automatically converted to the user's local system time so `11:59 PM` deadlines stay on the proper calendar day.
- **Input Validation:** Invalid time ranges, empty fields, malformed days, broken feed URLs, or offline states trigger clear user messages rather than unhandled crashes.

## Project Structure

```text
SchoolPlanner/
├── gui.py                      # Graphical interface (Tkinter)
├── main.py                     # Text menu
├── scheduler.py                # Week filter, schedule generation, busy hours, .ics export
├── estimator.py                # Hour estimates (stated duration, keywords, AI, default)
├── store_ics.py                # Check and save the Canvas calendar link
├── fetch.py                    # Download the calendar and create events.json
├── Process.py                  # Clean the calendar events
├── sample_data.py              # Demo calendar for testing
├── paths.py                    # Centralized file paths
├── data/duration_keywords.csv  # Keyword -> hours table
├── requirements.txt            # Project dependencies (icalendar, pandas, etc.)
└── files/                      # Created at runtime (gitignored): link, events, priorities,
                                # busy hours, schedule
```

## Impact of This Project

Canvas only displays final deadlines for assignments, which often leads to procrastination, stress, dread, and burnout—particularly for students who struggle with time management or have ADHD.

SchoolPlanner solves this by breaking work down into a customized schedule tailored to your free time and priority preferences. Our goal is to reduce student stress, build sustainable study habits, and improve academic performance.

## Limitations and Future Work

- **Default Estimates:** Rule-based estimates rely on general heuristics rather than individual pacing (defaulting to 1.5 hours when no keyword matches, though `duration_keywords.csv` can be customized).
- **Submission Status:** Canvas `.ics` feeds do not indicate whether an assignment has already been submitted, so finished tasks may still be scheduled unless their priority is lowered.
- **Future Work:** Expanding adaptive learning to calibrate estimates based on each student's actual working speed over time.

## Demo Video

- [Phase 3 demo (graphical interface)](PASTE-THE-NEW-VIDEO-LINK-HERE)
- [Phase 2 prototype demo](https://drive.google.com/file/d/1Zyqx58Io2WkDO-PwYeMSOpKwedRa0rbh/view?usp=sharing)
