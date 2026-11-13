# SchoolPlanner

### Plan your days, weeks, even your month!

## About the Project

SchoolPlanner is a Canvas homework planner. It reads your Canvas calendar, finds the assignments due in the next 7 days, estimates how long each one will take, and builds an hour-by-hour study schedule around the times you are already busy.

The estimates are **rule-based**: the program looks for a duration written in the assignment description (for example "Estimated time: 2 hours") and, if there is none, for keywords in the title such as "quiz", "essay" or "lab". It does not use AI models at the moment. AI-based estimation is listed under *Future work*.

You can use SchoolPlanner from a graphical window (`gui.py`) or from a text menu (`main.py`). Both use the same code underneath and the same saved data.

## Getting Started & Installation

Before doing anything else, clone the GitHub repository to your computer.

**Requirements:** Python 3.10 or newer. Tkinter, which the window uses, comes with the installers from python.org for Windows and macOS. (On macOS with Homebrew Python, run `brew install python-tk` once.)

### 1. Open Your Terminal or Command Prompt

* **Windows:** Press the **Windows Key**, type `cmd`, and open **Command Prompt**.
* **macOS:** Press **Command + Space** to open Spotlight, type `Terminal`, and press **Enter**.

### 2. Navigate to the Project Directory

Locate the `SchoolPlanner` folder on your computer and run the command corresponding to your operating system:

* **Windows (Command Prompt):**
  ```cmd
  cd C:\Users\"your name"\Downloads\SchoolPlanner
  ```
* **macOS (Terminal):**
  ```bash
  cd ~/Downloads/SchoolPlanner
  ```

You can also type `cd` with a space and drag the SchoolPlanner folder directly into the terminal/CMD window.

### 3. Install Required Dependencies

In the same terminal window, run the installation command:

* **Windows:**
  ```cmd
  pip install -r requirements.txt
  ```
* **macOS:**
  ```bash
  pip3 install -r requirements.txt
  ```

## Running the Program

Once the installation is complete, launch the application from the same terminal window.

**Graphical interface (recommended):**

* **Windows:** `python gui.py`
* **macOS:** `python3 gui.py`

**Text menu:**

* **Windows:** `python main.py`
* **macOS:** `python3 main.py`

### Quick tour (no Canvas account needed)

1. In the **1. Calendar** tab, click **Load sample calendar (demo)**.
2. In **2. Assignments**, select a task and set its priority.
3. In **3. Busy hours**, add the times you cannot study (for example Monday 08:00 to 14:00).
4. In **4. Schedule**, click **Generate schedule**, then **Export to Google Calendar (.ics)**.

To use your real calendar, open Canvas, go to **Calendar > Calendar Feed**, copy the link and paste it in the **1. Calendar** tab. The link is private: it is stored only on your computer (inside the `files/` folder, which is not uploaded to GitHub).

## Implemented Features

* Save your Canvas calendar link (the link is checked first; `webcal://` links are accepted).
* Download and clean the assignments from the Canvas calendar.
* Filter the assignments due in the next 7 days.
* Estimate the hours for each assignment from the description or from keywords (English and Spanish).
* Set a priority (low, normal, high) for each assignment.
* Save your weekly busy hours (add and delete them).
* Generate an hour-by-hour schedule in 30-minute blocks, from 08:00 to midnight, with at most 6 hours of homework per day.
* Export the schedule to a `.ics` file for Google Calendar, Apple Calendar or Outlook.
* Save all data locally so it is still there the next time you open the program.
* Graphical interface with four tabs, plus the original text menu.
* Sample calendar so the program can be tried without a Canvas account.

## How the Schedule is Built

1. Each assignment's work is spread over the days between today and its due date, so it is not left for the last night.
2. High-priority assignments choose their time slots first. For equal priority, the earliest due date goes first.
3. A block is never placed during your busy hours, in the past, or after the deadline.
4. If an assignment does not fit before its deadline, the program shows a warning with the hours that could not be scheduled.
5. If there is nothing left to schedule, the previously saved schedule is deleted so an outdated schedule is never shown or exported.

## Technical Decisions

* **Python libraries:** `pandas` reads and writes the CSV files and builds and prints the schedule table. `icalendar` reads the Canvas calendar feed and writes the exported `.ics` file. Everything else (Tkinter, `json`, `csv`, `re`, `datetime`, `urllib`, `threading`) is part of the standard library, so only two packages need to be installed.
* **Tkinter for the interface:** it comes with Python, so the program runs on any computer without extra installs. Downloads run in a background thread so the window never freezes.
* **Separated modules:** the window (`gui.py`) and the text menu (`main.py`) contain no scheduling logic; they call the same functions in `scheduler.py`, `estimator.py`, `store_ics.py` and `fetch.py`. This keeps the logic in one place and easy to test.
* **Plain files for persistence:** JSON for settings, calendar events and priorities; CSV for busy hours and the schedule. They are simple to open, read and fix by hand.
* **Editable estimation rules:** the keyword table is a CSV file (`data/duration_keywords.csv`), so new keywords and hours can be added without touching the code.
* **Time zones:** Canvas sends dates in UTC, so they are converted to the computer's local time. A deadline of 11:59 PM stays on the right day.
* **Input checks:** wrong times, empty fields, invalid days, a broken link or no internet show a message instead of crashing the program.

## Project Structure

```
SchoolPlanner/
├── gui.py                      # Graphical interface (Tkinter)
├── main.py                     # Text menu
├── scheduler.py                # Week filter, schedule generation, busy hours, .ics export
├── estimator.py                # Hour estimates (stated duration, keywords, default)
├── store_ics.py                # Check and save the Canvas calendar link
├── fetch.py                    # Download the calendar and create events.json
├── Process.py                  # Clean the calendar events
├── sample_data.py              # Demo calendar for testing
├── paths.py                    # All file locations in one place
├── data/duration_keywords.csv  # Keyword -> hours table
├── requirements.txt            # icalendar, pandas
└── files/                      # Created at run time (not uploaded): link, events, priorities,
                                # busy hours, schedule
```

## Impact of this project

Canvas only shows final deadlines for assignments, which leads to procrastination, stress, dread, and burnout. This affects especially students who struggle with time management or have ADHD.

SchoolPlanner solves this by building a customized schedule tailored to your free time and priority preferences. Our goal is to reduce student stress, build better habits, and boost academic performance across many students.

## Limitations and Future Work

* The estimates are general rules, not a prediction for each student. Assignments without a known keyword use a default of 1.5 hours, and the keyword table can be edited.
* Canvas does not tell us which assignments are already submitted, so the program may still schedule time for finished work. Lowering their priority is the current workaround.
* Planned: estimating hours with an AI model, and learning each student's real working speed over time.

## Demo Video

* [Phase 3 demo (graphical interface)](PASTE-THE-NEW-VIDEO-LINK-HERE)
* [Phase 2 prototype demo](https://drive.google.com/file/d/1Zyqx58Io2WkDO-PwYeMSOpKwedRa0rbh/view?usp=sharing)