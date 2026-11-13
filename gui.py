import json
import queue
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk
from urllib.error import URLError

import scheduler
import store_ics
import ai_assistant
from fetch import download_calendar, load_saved_url
from main import get_week_tasks
from paths import EVENTS_PATH, EXPORT_PATH, ICS_PATH, SCHEDULE_PATH
from Process import procesar_calendario_canvas
from sample_data import build_sample_calendar

APP_TITLE = "SchoolPlanner"
HEADING_FONT = ("TkDefaultFont", 13, "bold")

EXPECTED_ERRORS = (FileNotFoundError, json.JSONDecodeError, OSError, URLError, ValueError)

PRIORITY_NAMES = ["Low", "Normal", "High"]
TIME_CHOICES = [f"{hour:02d}:{minute:02d}" for hour in range(24) for minute in (0, 30)]

def set_status(app, message):
    """Show a short message in the bar at the bottom of the window."""
    app["status"].set(message)


def show_error(app, error):
    """Show an error dialog and mirror it in the status bar."""
    messagebox.showerror(APP_TITLE, str(error))
    set_status(app, "Something went wrong. See the message that was shown.")


def set_busy(app, busy):
    """Disable the long-running buttons (and show a wait cursor) while working."""
    state = "disabled" if busy else "normal"
    for button in app["busy_buttons"]:
        button.config(state=state)
    app["root"].config(cursor="watch" if busy else "")


def run_in_background(app, work, on_success):
    """Run work() in a thread so the window does not freeze while it runs.

    When it finishes, on_success(result) is called in the main thread. If
    work() raises an error, an error dialog is shown instead. A queue is used
    to hand the result back because Tkinter widgets must only be touched from
    the main thread.
    """
    results = queue.Queue()

    def worker():
        try:
            results.put(("ok", work()))
        except Exception as error:
            results.put(("error", error))

    def check_for_result():
        try:
            kind, value = results.get_nowait()
        except queue.Empty:
            app["root"].after(100, check_for_result)
            return
        set_busy(app, False)
        if kind == "ok":
            on_success(value)
        else:
            show_error(app, value)

    set_busy(app, True)
    threading.Thread(target=worker, daemon=True).start()
    check_for_result()


def make_table(parent, columns, tree_heading=None, height=12):
    """Create a Treeview table with a scrollbar and return the Treeview.

    columns is a list of (column_id, heading_text, width, alignment).
    If tree_heading is given, the first column can hold expandable group rows
    (used by the schedule to group blocks by day).
    """
    frame = ttk.Frame(parent)
    frame.pack(fill="both", expand=True)

    show = "headings" if tree_heading is None else "tree headings"
    tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show=show,
                        height=height, selectmode="browse")
    for column_id, heading, width, anchor in columns:
        tree.heading(column_id, text=heading)
        tree.column(column_id, width=width, anchor=anchor)
    if tree_heading is not None:
        tree.heading("#0", text=tree_heading)
        tree.column("#0", width=210)

    scrollbar = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)
    tree.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    return tree


def clear_table(tree):
    """Remove every row from a Treeview."""
    tree.delete(*tree.get_children())


def minutes_to_text(minutes):
    """Turn minutes after midnight (e.g. 570) into 'HH:MM' (09:30)."""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def describe_events():
    """Return a sentence saying how many events are currently saved."""
    try:
        with EVENTS_PATH.open("r", encoding="utf-8") as events_file:
            count = len(json.load(events_file))
    except (OSError, ValueError):
        return "No calendar loaded yet."
    return f"{count} events are saved on this computer."


def describe_ai_status():
    """Return a sentence indicating whether Gemini AI is available."""
    if ai_assistant.load_api_key():
        cache = ai_assistant.load_ai_cache()
        return f"✦ Gemini AI: Active ({len(cache)} assignment plans cached)"
    return "✦ Gemini AI: No API key found (files/geminikeys.json)"


def build_setup_tab(app, notebook):
    """Tab 1: paste the Canvas feed link, or load the demo calendar."""
    tab = ttk.Frame(notebook, padding=16)

    ttk.Label(tab, text="Step 1 - Connect your Canvas calendar", font=HEADING_FONT).pack(anchor="w")
    ttk.Label(
        tab, justify="left",
        text="In Canvas open Calendar > Calendar Feed, copy the link and paste it below.\n"
             "The link is private. It is only stored on this computer.",
    ).pack(anchor="w", pady=(4, 12))

    try:
        saved_url = load_saved_url()
    except EXPECTED_ERRORS:
        saved_url = ""
    url_var = tk.StringVar(value=saved_url)
    url_entry = ttk.Entry(tab, textvariable=url_var, width=80, show="*")
    url_entry.pack(anchor="w")

    show_var = tk.BooleanVar(value=False)

    def toggle_link_visibility():
        url_entry.config(show="" if show_var.get() else "*")

    ttk.Checkbutton(tab, text="Show link", variable=show_var,
                    command=toggle_link_visibility).pack(anchor="w", pady=4)

    info_label = ttk.Label(tab, text=describe_events())
    ai_status_label = ttk.Label(tab, text=describe_ai_status(), foreground="#5c32a8")

    def finish_loading(count, source):
        """Common ending for both ways of loading a calendar."""
        info_label.config(text=describe_events())
        ai_status_label.config(text=describe_ai_status())
        set_status(app, f"{count} events loaded from {source}.")
        app["notebook"].select(1)

    def on_download_clicked():
        url = store_ics.normalize_url(url_var.get())
        if not url:
            messagebox.showerror(APP_TITLE, "Paste your Canvas calendar link first.")
            return
        set_status(app, "Checking the link...")
        run_in_background(app, lambda: store_ics.validate_ics_url(url),
                          lambda link_ok: after_link_check(url, link_ok))

    def after_link_check(url, link_ok):
        if not link_ok and not messagebox.askyesno(
                APP_TITLE,
                "That link could not be verified (typo, no internet, or not an .ics feed).\n\n"
                "Save it and try anyway?"):
            set_status(app, "Nothing was saved.")
            return
        set_status(app, "Downloading your calendar...")
        run_in_background(app, lambda: save_and_load(url),
                          lambda count: finish_loading(count, "Canvas"))

    def save_and_load(url):
        store_ics.save_url(url)
        download_calendar(url)
        return procesar_calendario_canvas(ICS_PATH, EVENTS_PATH)

    def on_sample_clicked():
        try:
            build_sample_calendar(ICS_PATH)
            count = procesar_calendario_canvas(ICS_PATH, EVENTS_PATH)
        except EXPECTED_ERRORS as error:
            show_error(app, error)
            return
        finish_loading(count, "the sample calendar")

    buttons = ttk.Frame(tab)
    buttons.pack(anchor="w", pady=12)
    download_button = ttk.Button(buttons, text="Save link and download calendar",
                                 command=on_download_clicked)
    sample_button = ttk.Button(buttons, text="Load sample calendar (demo)",
                               command=on_sample_clicked)
    download_button.pack(side="left", padx=(0, 8))
    sample_button.pack(side="left")
    app["busy_buttons"] += [download_button, sample_button]

    info_label.pack(anchor="w", pady=(8, 0))
    ai_status_label.pack(anchor="w", pady=(2, 0))

    # Gemini API Key section
    ttk.Separator(tab, orient="horizontal").pack(fill="x", pady=(16, 12))
    ttk.Label(tab, text="Google AI Studio Gemini API Key", font=HEADING_FONT).pack(anchor="w")
    ttk.Label(
        tab, justify="left",
        text="Optional: Enter your API key to enable AI workload estimation and step-by-step action plans.\n"
             "Stored locally in files/geminikeys.json with 'key' as the only entry.",
    ).pack(anchor="w", pady=(4, 8))

    saved_key = ai_assistant.load_api_key() or ""
    key_var = tk.StringVar(value=saved_key)

    key_row = ttk.Frame(tab)
    key_row.pack(anchor="w", fill="x")

    key_entry = ttk.Entry(key_row, textvariable=key_var, width=54, show="*")
    key_entry.pack(side="left", padx=(0, 8))

    def on_save_key():
        new_key = key_var.get().strip()
        try:
            ai_assistant.save_api_key(new_key)
            ai_status_label.config(text=describe_ai_status())
            set_status(app, "Gemini API key saved to files/geminikeys.json.")
            messagebox.showinfo(APP_TITLE, "Gemini API key saved.")
        except Exception as error:
            show_error(app, error)

    save_key_button = ttk.Button(key_row, text="Save", command=on_save_key)
    save_key_button.pack(side="left", padx=(0, 8))

    show_key_var = tk.BooleanVar(value=False)

    def toggle_key_visibility():
        key_entry.config(show="" if show_key_var.get() else "*")

    ttk.Checkbutton(key_row, text="Show key", variable=show_key_var,
                    command=toggle_key_visibility).pack(side="left")

    return tab


def show_ai_dialog(app, task, on_applied):
    """Modal dialog displaying the Gemini AI workload estimate and action plan checklist."""
    dialog = tk.Toplevel(app["root"])
    dialog.title(f"Gemini AI Plan - {task['title']}")
    dialog.geometry("620x540")
    dialog.minsize(500, 420)
    dialog.transient(app["root"])
    dialog.grab_set()

    content = ttk.Frame(dialog, padding=16)
    content.pack(fill="both", expand=True)

    header_frame = ttk.Frame(content)
    header_frame.pack(fill="x", pady=(0, 10))
    ttk.Label(header_frame, text=f"✦ Gemini AI Plan: {task['course']}", font=HEADING_FONT, foreground="#5c32a8").pack(anchor="w")
    ttk.Label(header_frame, text=task["title"], font=("TkDefaultFont", 11, "bold")).pack(anchor="w", pady=(2, 0))
    due_str = task["due"].strftime("%a %m-%d %H:%M") if hasattr(task["due"], "strftime") else str(task["due"])
    ttk.Label(header_frame, text=f"Due: {due_str} | Current estimate: {task['hours']:g} h ({task['source']})").pack(anchor="w")

    body_frame = ttk.Frame(content)
    body_frame.pack(fill="both", expand=True)

    def render_analysis(analysis):
        for widget in body_frame.winfo_children():
            widget.destroy()

        hours = analysis.get("estimated_hours", task["hours"])
        reasoning = analysis.get("reasoning", "No rationale provided.")
        subtasks = analysis.get("subtasks", [])

        card = ttk.LabelFrame(body_frame, text=" Recommended Workload ", padding=10)
        card.pack(fill="x", pady=(0, 10))

        work_row = ttk.Frame(card)
        work_row.pack(fill="x")
        ttk.Label(work_row, text=f"{hours:g} hours", font=("TkDefaultFont", 14, "bold"), foreground="#5c32a8").pack(side="left")

        def apply_hours():
            try:
                ai_assistant.apply_ai_estimate(task["id"], hours)
            except Exception as err:
                messagebox.showerror(APP_TITLE, f"Could not apply hours: {err}")
                return
            on_applied()
            set_status(app, f"Applied AI workload ({hours:g} h) to '{task['title']}'.")
            dialog.destroy()

        apply_btn = ttk.Button(work_row, text=f"Apply {hours:g} Hours to Schedule", command=apply_hours)
        apply_btn.pack(side="right")

        ttk.Label(card, text=f"Rationale: {reasoning}", wraplength=560, justify="left").pack(anchor="w", pady=(6, 0))

        plan_frame = ttk.LabelFrame(body_frame, text=f" Action Plan Checklist ({len(subtasks)} milestones) ", padding=10)
        plan_frame.pack(fill="both", expand=True, pady=(0, 10))

        text_container = ttk.Frame(plan_frame)
        text_container.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(text_container, orient="vertical")
        text_widget = tk.Text(text_container, wrap="word", yscrollcommand=scrollbar.set,
                              font=("TkDefaultFont", 10), padx=8, pady=8)
        scrollbar.config(command=text_widget.yview)
        scrollbar.pack(side="right", fill="y")
        text_widget.pack(side="left", fill="both", expand=True)

        for idx, step in enumerate(subtasks, start=1):
            text_widget.insert("end", f"[{idx}]  {step}\n\n")
        text_widget.config(state="disabled")

        btn_bar = ttk.Frame(body_frame)
        btn_bar.pack(fill="x", pady=(6, 0))

        ttk.Button(btn_bar, text="Close", command=dialog.destroy).pack(side="left")
        ttk.Button(btn_bar, text="↻ Re-analyze with Gemini", command=lambda: start_analysis(force_refresh=True)).pack(side="right")

    def show_loading():
        for widget in body_frame.winfo_children():
            widget.destroy()
        loading_frame = ttk.Frame(body_frame, padding=30)
        loading_frame.pack(fill="both", expand=True)
        ttk.Label(loading_frame, text="Analyzing assignment instructions with Gemini AI...",
                  font=("TkDefaultFont", 11, "bold"), foreground="#5c32a8").pack(pady=(20, 4))
        ttk.Label(loading_frame, text="Evaluating workload complexity, duration, and actionable milestones...").pack()
        progress = ttk.Progressbar(loading_frame, mode="indeterminate", length=240)
        progress.pack(pady=16)
        progress.start(15)

    def start_analysis(force_refresh=False):
        has_key = ai_assistant.load_api_key() is not None
        cache = ai_assistant.load_ai_cache()
        cached_entry = cache.get(task["id"])

        if not force_refresh and cached_entry:
            render_analysis(cached_entry)
            return

        if not has_key:
            messagebox.showerror(
                APP_TITLE,
                "No Gemini API key found.\n\n"
                "Please place your Google AI Studio API key in files/geminikeys.json "
                "or set the GEMINI_API_KEY environment variable."
            )
            dialog.destroy()
            return

        show_loading()

        def do_work():
            events = scheduler.load_events()
            target_event = next((ev for ev in events if ev.get("id_evento") == task["id"]), None)
            description = target_event.get("descripcion", "") if target_event else ""
            return ai_assistant.analyze_assignment(
                task["id"],
                task["title"],
                task["course"],
                description,
                force_refresh=True,
            )

        def worker():
            try:
                res = do_work()
                dialog.after(0, lambda: render_analysis(res))
            except Exception as e:
                dialog.after(0, lambda: on_error(e))

        def on_error(err):
            for widget in body_frame.winfo_children():
                widget.destroy()
            err_frame = ttk.Frame(body_frame, padding=20)
            err_frame.pack(fill="both", expand=True)
            ttk.Label(err_frame, text="AI Analysis Failed", font=HEADING_FONT, foreground="#cc0000").pack(pady=(10, 4))
            ttk.Label(err_frame, text=str(err), wraplength=500, justify="center").pack(pady=(0, 16))
            ttk.Button(err_frame, text="Retry Analysis", command=lambda: start_analysis(force_refresh=True)).pack(pady=4)
            ttk.Button(err_frame, text="Close", command=dialog.destroy).pack(pady=4)

        threading.Thread(target=worker, daemon=True).start()

    start_analysis(force_refresh=False)


def build_assignments_tab(app, notebook):
    """Tab 2: table of this week's assignments, with priority selector, manual hours editing, and Gemini AI plan."""
    tab = ttk.Frame(notebook, padding=16)
    ttk.Label(tab, text="Step 2 - This week's assignments", font=HEADING_FONT).pack(anchor="w")
    hint_label = ttk.Label(tab, text="")
    hint_label.pack(anchor="w", pady=(4, 8))

    columns = [("due", "Due", 125, "w"), ("course", "Course", 85, "w"),
               ("title", "Assignment", 240, "w"), ("hours", "Est. hours", 75, "center"),
               ("source", "Estimated from", 140, "w"), ("priority", "Priority", 70, "center"),
               ("ai_plan", "AI Plan", 75, "center")]
    tree = make_table(tab, columns)

    # Inline hours editor (Entry widget floated over the treeview)
    hours_entry_var = tk.StringVar()
    hours_entry = ttk.Entry(tree, textvariable=hours_entry_var, width=7, justify="center")
    _editing_iid = [None]  # mutable ref to current item being edited

    def show_hours_editor(iid, current_hours):
        """Position an Entry widget over the Est. hours cell for the given row."""
        hours_entry_var.set(f"{current_hours:g}")
        bbox = tree.bbox(iid, column="hours")
        if not bbox:
            return
        x, y, w, h = bbox
        hours_entry.place(x=x, y=y, width=max(w, 60), height=h)
        hours_entry.focus_set()
        hours_entry.select_range(0, "end")
        _editing_iid[0] = iid

    def hide_hours_editor():
        hours_entry.place_forget()
        _editing_iid[0] = None

    def commit_hours_edit(event=None):
        iid = _editing_iid[0]
        if iid is None:
            return
        try:
            value = float(hours_entry_var.get().strip().replace(",", "."))
            if not (0.5 <= value <= 24.0):
                raise ValueError("out of range")
        except ValueError:
            messagebox.showerror(APP_TITLE, "Enter a number between 0.5 and 24.")
            hide_hours_editor()
            return
        position = int(iid)
        task = app["tasks"][position]
        try:
            actual = ai_assistant.set_manual_hours(task["id"], value)
        except Exception as err:
            show_error(app, err)
            hide_hours_editor()
            return
        hide_hours_editor()
        refresh()
        tree.selection_set(str(position))
        set_status(app, f"Set '{task['title']}' to {actual:g} hours (manual).")

    def cancel_hours_edit(event=None):
        hide_hours_editor()

    hours_entry.bind("<Return>", commit_hours_edit)
    hours_entry.bind("<KP_Enter>", commit_hours_edit)
    hours_entry.bind("<Escape>", cancel_hours_edit)
    hours_entry.bind("<FocusOut>", cancel_hours_edit)

    controls = ttk.Frame(tab)
    controls.pack(fill="x", pady=(10, 0))
    ttk.Label(controls, text="Priority:").pack(side="left")
    priority_box = ttk.Combobox(controls, values=PRIORITY_NAMES, state="readonly", width=8)
    priority_box.current(1)
    priority_box.pack(side="left", padx=4)

    def apply_priority():
        selection = tree.selection()
        if not selection:
            messagebox.showinfo(APP_TITLE, "Click an assignment in the table first.")
            return
        position = int(selection[0])
        task = app["tasks"][position]
        level = priority_box.current() + 1
        try:
            scheduler.save_priority(task["id"], level)
        except EXPECTED_ERRORS as error:
            show_error(app, error)
            return
        refresh()
        tree.selection_set(str(position))
        set_status(app, f"'{task['title']}' is now {PRIORITY_NAMES[level - 1].lower()} priority.")

    ttk.Button(controls, text="Apply priority", command=apply_priority).pack(side="left", padx=(0, 8))

    def edit_hours():
        selection = tree.selection()
        if not selection:
            messagebox.showinfo(APP_TITLE, "Click an assignment in the table first.")
            return
        position = int(selection[0])
        task = app["tasks"][position]
        show_hours_editor(str(position), task["hours"])

    ttk.Button(controls, text="✎ Edit Hours", command=edit_hours).pack(side="left", padx=(0, 8))

    def open_ai_plan():
        selection = tree.selection()
        if not selection:
            messagebox.showinfo(APP_TITLE, "Click an assignment in the table first.")
            return
        position = int(selection[0])
        task = app["tasks"][position]
        show_ai_dialog(app, task, on_applied=refresh)

    ai_button = ttk.Button(controls, text="✦ AI Plan & Estimate", command=open_ai_plan)
    ai_button.pack(side="left")

    total_label = ttk.Label(controls, text="")
    total_label.pack(side="right")

    def refresh():
        """Reload the table from the saved calendar and priorities."""
        hide_hours_editor()
        clear_table(tree)
        try:
            tasks = get_week_tasks()
        except EXPECTED_ERRORS:
            tasks = []
            hint_label.config(text="No calendar loaded yet. Go to step 1 first.")
        else:
            hint_label.config(
                text="" if tasks else "No assignments are due in the next 7 days.")
        app["tasks"] = tasks

        ai_cache = ai_assistant.load_ai_cache()
        for position, task in enumerate(tasks):
            priority = scheduler.PRIORITY_LABELS.get(task["priority"], "normal")
            has_plan = "Ready" if task["id"] in ai_cache else "-"
            tree.insert("", "end", iid=str(position), values=(
                task["due"].strftime("%a %m-%d %H:%M"), task["course"], task["title"],
                f"{task['hours']:g}", task["source"], priority.capitalize(), has_plan))
        total = sum(task["hours"] for task in tasks)
        total_label.config(text=f"Total estimated work: {total:g} hours")

    def on_row_selected(_event):
        """Show the selected assignment's current priority in the selector."""
        selection = tree.selection()
        if selection:
            priority_box.current(app["tasks"][int(selection[0])]["priority"] - 1)

    def on_double_click(event):
        """Double-click on Est. hours column to edit; on other columns open AI plan."""
        region = tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col = tree.identify_column(event.x)
        iid = tree.identify_row(event.y)
        if not iid:
            return
        if col == "#4":  # Est. hours column (1-indexed, #0 is tree col)
            position = int(iid)
            task = app["tasks"][position]
            show_hours_editor(iid, task["hours"])
        else:
            open_ai_plan()

    tree.bind("<<TreeviewSelect>>", on_row_selected)
    tree.bind("<Double-1>", on_double_click)

    app["refreshers"]["assignments"] = refresh
    refresh()
    return tab


def build_busy_hours_tab(app, notebook):
    """Tab 3: weekly blocks when the student is NOT available."""
    tab = ttk.Frame(notebook, padding=16)
    ttk.Label(tab, text="Step 3 - Your busy hours", font=HEADING_FONT).pack(anchor="w")
    ttk.Label(tab, text="Add the weekly times you cannot do homework (classes, work, sports...).",
              ).pack(anchor="w", pady=(4, 8))

    form = ttk.Frame(tab)
    form.pack(anchor="w", pady=(0, 8))
    ttk.Label(form, text="Day").grid(row=0, column=0, sticky="w")
    ttk.Label(form, text="From (HH:MM)").grid(row=0, column=1, sticky="w", padx=8)
    ttk.Label(form, text="To (HH:MM)").grid(row=0, column=2, sticky="w", padx=8)
    day_box = ttk.Combobox(form, values=scheduler.DAY_NAMES, state="readonly", width=12)
    day_box.current(0)
    start_box = ttk.Combobox(form, values=TIME_CHOICES, width=8)
    end_box = ttk.Combobox(form, values=TIME_CHOICES, width=8)
    start_box.set("08:00")
    end_box.set("10:00")
    day_box.grid(row=1, column=0)
    start_box.grid(row=1, column=1, padx=8)
    end_box.grid(row=1, column=2, padx=8)

    tree = make_table(tab, [("day", "Day", 140, "w"), ("start", "From", 90, "center"),
                            ("end", "To", 90, "center")], height=10)
    note_label = ttk.Label(tab, text="", foreground="#a15c00")
    note_label.pack(anchor="w", pady=(6, 0))

    def refresh():
        """Reload the table from busy_hours.csv."""
        clear_table(tree)
        blocks, skipped_rows = scheduler.load_busy_hours()
        for position, (weekday, start, end) in enumerate(blocks):
            tree.insert("", "end", iid=str(position), values=(
                scheduler.DAY_NAMES[weekday], minutes_to_text(start), minutes_to_text(end)))
        if skipped_rows:
            note_label.config(text="Ignored invalid rows in busy_hours.csv: " + "; ".join(skipped_rows))
        else:
            note_label.config(text="" if blocks else "No busy hours yet: every hour counts as free.")

    def add_block():
        try:
            scheduler.add_busy_hour(day_box.get(), start_box.get(), end_box.get())
        except ValueError as error:
            messagebox.showerror(APP_TITLE, f"Could not save that block.\n\n{error}\n\n"
                                            "Use 24-hour times such as 08:30, and make sure "
                                            "the end is after the start.")
            return
        except OSError as error:
            show_error(app, error)
            return
        refresh()
        set_status(app, f"Busy block added: {day_box.get()} {start_box.get()}-{end_box.get()}.")

    def delete_block():
        selection = tree.selection()
        if not selection:
            messagebox.showinfo(APP_TITLE, "Click a busy block in the table first.")
            return
        try:
            scheduler.delete_busy_hour(int(selection[0]))
        except EXPECTED_ERRORS as error:
            show_error(app, error)
            return
        refresh()
        set_status(app, "Busy block deleted.")

    buttons = ttk.Frame(tab)
    buttons.pack(anchor="w", pady=(8, 0))
    ttk.Button(buttons, text="Add busy block", command=add_block).pack(side="left", padx=(0, 8))
    ttk.Button(buttons, text="Delete selected", command=delete_block).pack(side="left")

    app["refreshers"]["busy"] = refresh
    refresh()
    return tab


def build_schedule_tab(app, notebook):
    """Tab 4: generate, view and export the homework schedule."""
    tab = ttk.Frame(notebook, padding=16)
    ttk.Label(tab, text="Step 4 - Your homework schedule", font=HEADING_FONT).pack(anchor="w")

    buttons = ttk.Frame(tab)
    buttons.pack(anchor="w", pady=(8, 8))

    columns = [("start", "From", 70, "center"), ("end", "To", 70, "center"),
               ("hours", "Hours", 60, "center"), ("course", "Course", 90, "w"),
               ("assignment", "Assignment", 280, "w"), ("priority", "Priority", 80, "center")]
    tree = make_table(tab, columns, tree_heading="Day", height=14)
    tree.tag_configure("day", font=("TkDefaultFont", 10, "bold"))

    summary_label = ttk.Label(tab, text="")
    summary_label.pack(anchor="w", pady=(8, 0))
    notes_label = ttk.Label(tab, text="", foreground="#a15c00", justify="left", wraplength=840)
    notes_label.pack(anchor="w")

    def show_schedule(schedule):
        """Fill the table, grouping the blocks by day."""
        clear_table(tree)
        if schedule.empty:
            summary_label.config(text="No schedule yet. Click 'Generate schedule'.")
            return
        for date_text, day_rows in schedule.groupby("date"):
            day_total = day_rows["hours"].sum()
            group = tree.insert("", "end", open=True, tags=("day",),
                                text=f"{day_rows['day'].iloc[0]} {date_text}  ({day_total:g} h)")
            for _, row in day_rows.iterrows():
                tree.insert(group, "end", values=(row["start"], row["end"], f"{row['hours']:g}",
                                                  row["course"], row["assignment"],
                                                  str(row["priority"]).capitalize()))
        summary_label.config(
            text=f"{len(schedule)} study blocks, {schedule['hours'].sum():g} hours in total. "
                 f"Saved in {SCHEDULE_PATH.name}.")

    def refresh():
        """Show the schedule that was saved by the last run."""
        show_schedule(scheduler.load_schedule())

    def generate():
        try:
            tasks = get_week_tasks()
            busy_blocks, skipped_rows = scheduler.load_busy_hours()
        except EXPECTED_ERRORS as error:
            show_error(app, error)
            return

        schedule, warnings = scheduler.build_schedule(tasks, busy_blocks, datetime.now())
        notes = list(warnings)
        notes += [f"Ignored busy-hour {message}" for message in skipped_rows]
        if not busy_blocks:
            notes.append("No busy hours saved, so every hour counts as free (step 3).")

        if schedule.empty:
            scheduler.clear_schedule()
            notes.append("The previously saved schedule was cleared because it no longer applies.")
            set_status(app, "No study blocks to schedule.")
        else:
            try:
                scheduler.save_schedule(schedule)
            except OSError as error:
                show_error(app, error)
                return
            set_status(app, f"Schedule generated: {len(schedule)} study blocks.")
        show_schedule(schedule)
        notes_label.config(text="\n".join(notes))

    def export():
        schedule = scheduler.load_schedule()
        if schedule.empty:
            messagebox.showinfo(APP_TITLE, "There is no saved schedule to export. "
                                           "Click 'Generate schedule' first.")
            return
        try:
            count = scheduler.export_schedule_ics(schedule)
        except OSError as error:
            show_error(app, error)
            return
        set_status(app, f"{count} study blocks exported.")
        messagebox.showinfo(APP_TITLE, f"{count} study blocks exported to:\n{EXPORT_PATH}\n\n"
                                       "In Google Calendar: Settings > Import & export > Import, "
                                       "then choose that file.")

    ttk.Button(buttons, text="Generate schedule", command=generate).pack(side="left", padx=(0, 8))
    ttk.Button(buttons, text="Export to Google Calendar (.ics)", command=export).pack(side="left")

    app["refreshers"]["schedule"] = refresh
    refresh()
    return tab


def enable_sharp_text():
    """On Windows, ask for high-DPI mode so the text is not blurry."""
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except (ImportError, AttributeError, OSError):
        pass


def build_window():
    """Create the main window with its four tabs and the status bar."""
    enable_sharp_text()
    root = tk.Tk()
    root.title(APP_TITLE)
    root.geometry("940x620")
    root.minsize(800, 520)
    ttk.Style().configure("Treeview", rowheight=24)

    app = {"root": root, "status": tk.StringVar(value="Welcome! Start with step 1."),
           "busy_buttons": [], "refreshers": {}, "tasks": []}

    notebook = ttk.Notebook(root)
    app["notebook"] = notebook
    notebook.add(build_setup_tab(app, notebook), text="1. Calendar")
    notebook.add(build_assignments_tab(app, notebook), text="2. Assignments")
    notebook.add(build_busy_hours_tab(app, notebook), text="3. Busy hours")
    notebook.add(build_schedule_tab(app, notebook), text="4. Schedule")
    notebook.pack(fill="both", expand=True, padx=8, pady=(8, 0))

    ttk.Label(root, textvariable=app["status"], relief="sunken", anchor="w",
              padding=(8, 3)).pack(fill="x", side="bottom", padx=8, pady=8)

    tab_refreshers = [None, "assignments", "busy", "schedule"]

    def on_tab_changed(_event):
        name = tab_refreshers[notebook.index("current")]
        if name:
            app["refreshers"][name]()

    notebook.bind("<<NotebookTabChanged>>", on_tab_changed)
    return root


def main():
    """Open the window and wait for the user."""
    build_window().mainloop()


if __name__ == "__main__":
    main()