"""
Tray calendar app, cleaner structure (macOS + Windows)

    pip install PySide6
    pip install pyobjc-framework-Cocoa      # macOS only: hides the Dock icon
    python tray_calendar_clean.py

Layers (each one knows as little as possible about the others):
    Store        data only (SQLite). No Qt widgets.
    EntryDialog  add/edit window. Returns values, knows nothing about storage.
    Popover      the tray window. A dumb view: shows data, emits signals.
    TrayApp      controller. Wires tray + popover + dialog + store together.
"""
import sqlite3
import sys
import time
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QDate, QPointF, QRectF, QStandardPaths, Qt, QTimer, Signal
from PySide6.QtGui import (QColor, QCursor, QFont, QIcon, QPainter, QPainterPath,
                           QPen, QPixmap, QPolygonF, QTextCharFormat)
from PySide6.QtWidgets import (
    QApplication, QCalendarWidget, QDialog, QDialogButtonBox, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMenu,
    QPushButton, QSystemTrayIcon, QToolButton, QVBoxLayout, QWidget,
)

IS_MAC = sys.platform == "darwin"
RADIUS, ARROW_H, ARROW_W, PAD = 14, 10, 22, 12

STYLE = """
QLabel { color: white; }
QLabel#month { font-size: 15px; font-weight: 600; }
QPushButton#new { background: #7a4fd6; color: white; border: none;
                  border-radius: 8px; padding: 7px 14px; font-weight: 600; }
QPushButton#new:hover { background: #8b63e6; }
QToolButton { color: #ddd; border: none; font-size: 15px; padding: 4px 10px; }
QToolButton:hover { background: rgba(255,255,255,30); border-radius: 6px; }
QCalendarWidget QWidget { color: white; background: transparent; }
QCalendarWidget QAbstractItemView { color: white; background: transparent;
    selection-background-color: #7a4fd6; selection-color: white; outline: 0; }
QListWidget { background: transparent; border: none; color: white; font-size: 14px; }
QListWidget::item { padding: 8px 4px; border-bottom: 1px solid rgba(255,255,255,25); }
QListWidget::item:selected { background: rgba(122,79,214,120); }
"""


# ============================================================ platform helpers
def hide_dock_icon():
    """macOS: behave like a menu bar app (no Dock icon)."""
    if not IS_MAC:
        return
    try:
        from AppKit import NSApplication, NSApplicationActivationPolicyAccessory
        NSApplication.sharedApplication().setActivationPolicy_(
            NSApplicationActivationPolicyAccessory)
    except ImportError:
        pass  # pip install pyobjc-framework-Cocoa


def bring_to_front(widget: QWidget):
    widget.show()
    widget.raise_()
    widget.activateWindow()
    if IS_MAC:  # menu-bar apps aren't "active", so windows can open behind others
        try:
            from AppKit import NSApplication
            NSApplication.sharedApplication().activateIgnoringOtherApps_(True)
        except ImportError:
            pass


def make_icon() -> QIcon:
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).parent))  # _MEIPASS = PyInstaller bundle
    icon = QIcon(str(base / "icon.png"))
    if IS_MAC:
        icon.setIsMask(True)  # optional: treat it as a monochrome template icon
    return icon


# ============================================================ data layer
@dataclass
class Entry:
    id: int
    day: str      # "yyyy-MM-dd"
    title: str
    notes: str


class Store:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.execute(
            "CREATE TABLE IF NOT EXISTS entries ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, day TEXT NOT NULL, "
            "title TEXT NOT NULL, notes TEXT NOT NULL DEFAULT '')")
        self.db.commit()

    def get(self, entry_id: int):
        row = self.db.execute(
            "SELECT id, day, title, notes FROM entries WHERE id = ?", (entry_id,)).fetchone()
        return Entry(*row) if row else None

    def for_day(self, day: str) -> list:
        rows = self.db.execute(
            "SELECT id, day, title, notes FROM entries WHERE day = ? ORDER BY id", (day,))
        return [Entry(*r) for r in rows]

    def days_with_entries(self) -> set:
        return {r[0] for r in self.db.execute("SELECT DISTINCT day FROM entries")}

    def add(self, day: str, title: str, notes: str):
        self.db.execute("INSERT INTO entries (day, title, notes) VALUES (?, ?, ?)",
                        (day, title, notes))
        self.db.commit()

    def update(self, entry_id: int, title: str, notes: str):
        self.db.execute("UPDATE entries SET title = ?, notes = ? WHERE id = ?",
                        (title, notes, entry_id))
        self.db.commit()

    def delete(self, entry_id: int):
        self.db.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
        self.db.commit()


# ============================================================ add / edit window
class EntryDialog(QDialog):
    SAVED = 1    # same value as QDialog.Accepted
    DELETE = 2   # custom result code

    def __init__(self, date: QDate, entry: Entry = None):
        super().__init__()
        self.setWindowTitle("Edit entry" if entry else "Add entry")
        self.setMinimumWidth(340)
        self.setWindowFlag(Qt.WindowStaysOnTopHint, True)

        self.title_edit = QLineEdit(entry.title if entry else "")
        self.notes_edit = QLineEdit(entry.notes if entry else "")

        form = QFormLayout()
        form.addRow("Date", QLabel(date.toString("dddd, d MMM yyyy")))
        form.addRow("Title", self.title_edit)
        form.addRow("Notes", self.notes_edit)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        if entry:
            delete_btn = buttons.addButton("Delete", QDialogButtonBox.DestructiveRole)
            delete_btn.clicked.connect(lambda: self.done(self.DELETE))

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def values(self):
        return (self.title_edit.text().strip() or "Untitled", self.notes_edit.text().strip())


# ============================================================ tray window (view only)
class Popover(QWidget):
    add_requested = Signal(QDate)
    edit_requested = Signal(int)      # entry id
    date_changed = Signal()
    quit_requested = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint | Qt.NoDropShadowWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet(STYLE)
        self.setFixedSize(380, 500)

        self.arrow_up = True
        self.arrow_x = self.width() / 2
        self._last_hide = 0.0

        # row 1: [+ New] ........ [Quit]
        new_btn = QPushButton("+  New")
        new_btn.setObjectName("new")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(lambda: self.add_requested.emit(self.selected_date()))
        quit_btn = QToolButton()
        quit_btn.setText("Quit")
        quit_btn.clicked.connect(self.quit_requested)
        row1 = QHBoxLayout()
        row1.addWidget(new_btn)
        row1.addStretch()
        row1.addWidget(quit_btn)

        # row 2: custom month navigation (the built-in one uses nested popups)
        prev_btn, next_btn, today_btn = QToolButton(), QToolButton(), QToolButton()
        prev_btn.setText("‹")
        next_btn.setText("›")
        today_btn.setText("Today")
        self.month_label = QLabel(alignment=Qt.AlignCenter)
        self.month_label.setObjectName("month")
        row2 = QHBoxLayout()
        row2.addWidget(prev_btn)
        row2.addWidget(self.month_label, 1)
        row2.addWidget(next_btn)
        row2.addWidget(today_btn)

        self.calendar = QCalendarWidget()
        self.calendar.setNavigationBarVisible(False)
        self.calendar.setGridVisible(False)
        self.calendar.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader)
        self.calendar.selectionChanged.connect(self.date_changed)
        self.calendar.currentPageChanged.connect(self._update_month_label)
        prev_btn.clicked.connect(self.calendar.showPreviousMonth)
        next_btn.clicked.connect(self.calendar.showNextMonth)
        today_btn.clicked.connect(lambda: self.calendar.setSelectedDate(QDate.currentDate()))
        self._update_month_label(self.calendar.yearShown(), self.calendar.monthShown())

        self.list = QListWidget()
        self.list.itemDoubleClicked.connect(
            lambda item: self.edit_requested.emit(item.data(Qt.UserRole)))

        self.root = QVBoxLayout(self)
        self.root.setSpacing(8)
        self.root.addLayout(row1)
        self.root.addLayout(row2)
        self.root.addWidget(self.calendar)
        self.root.addWidget(self.list, 1)

    # ----- API used by the controller
    def selected_date(self) -> QDate:
        return self.calendar.selectedDate()

    def set_entries(self, entries):
        self.list.clear()
        for e in entries:
            item = QListWidgetItem(f"{e.title}\n{e.notes}" if e.notes else e.title)
            item.setData(Qt.UserRole, e.id)
            self.list.addItem(item)

    def mark_days(self, days):
        self.calendar.setDateTextFormat(QDate(), QTextCharFormat())  # clears all
        fmt = QTextCharFormat()
        fmt.setFontWeight(QFont.Bold)
        fmt.setFontUnderline(True)
        fmt.setForeground(QColor("#b79cff"))
        for d in days:
            self.calendar.setDateTextFormat(QDate.fromString(d, Qt.ISODate), fmt)

    def toggle_near(self, tray: QSystemTrayIcon):
        # Qt.Popup closes itself when the tray icon is clicked, then the click
        # arrives here. Ignore it, otherwise the popover would instantly reopen.
        if time.monotonic() - self._last_hide < 0.25:
            return
        self._place_near(tray)
        bring_to_front(self)

    # ----- internals
    def _update_month_label(self, year, month):
        self.month_label.setText(QDate(year, month, 1).toString("MMMM yyyy"))

    def hideEvent(self, e):
        self._last_hide = time.monotonic()
        super().hideEvent(e)

    def _place_near(self, tray):
        geo = tray.geometry()
        if geo.isEmpty():  # some systems don't report it: fall back to the cursor
            pos = QCursor.pos()
            cx, a_top, a_bottom = pos.x(), pos.y(), pos.y()
        else:
            cx, a_top, a_bottom = geo.center().x(), geo.top(), geo.bottom()

        screen = QApplication.screenAt(QCursor.pos()) or QApplication.primaryScreen()
        avail = screen.availableGeometry()

        self.arrow_up = a_top < screen.geometry().center().y()  # bar on top = macOS
        self.root.setContentsMargins(
            PAD, ARROW_H + PAD if self.arrow_up else PAD,
            PAD, PAD if self.arrow_up else ARROW_H + PAD)

        x = cx - self.width() // 2
        x = max(avail.left() + 4, min(x, avail.right() - self.width() - 4))
        y = a_bottom + 2 if self.arrow_up else a_top - self.height() - 2
        self.arrow_x = cx - x
        self.move(x, y)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        top = ARROW_H if self.arrow_up else 0
        bottom = h if self.arrow_up else h - ARROW_H
        body = QRectF(1, top + 1, w - 2, bottom - top - 2)

        path = QPainterPath()
        path.addRoundedRect(body, RADIUS, RADIUS)

        ax = min(max(self.arrow_x, RADIUS + ARROW_W), w - RADIUS - ARROW_W)
        if self.arrow_up:
            tri = QPolygonF([QPointF(ax - ARROW_W / 2, body.top()),
                             QPointF(ax, body.top() - ARROW_H + 1),
                             QPointF(ax + ARROW_W / 2, body.top())])
        else:
            tri = QPolygonF([QPointF(ax - ARROW_W / 2, body.bottom()),
                             QPointF(ax, body.bottom() + ARROW_H - 1),
                             QPointF(ax + ARROW_W / 2, body.bottom())])
        arrow = QPainterPath()
        arrow.addPolygon(tri)
        arrow.closeSubpath()

        p.setPen(QPen(QColor(255, 255, 255, 40), 1))
        p.setBrush(QColor(40, 40, 44, 250))
        p.drawPath(path.united(arrow))


# ============================================================ controller
class TrayApp:
    def __init__(self, app: QApplication):
        data_dir = Path(QStandardPaths.writableLocation(QStandardPaths.AppDataLocation))
        self.store = Store(data_dir / "entries.db")
        self.popover = Popover()
        self.dialog = None

        self.tray = QSystemTrayIcon(make_icon())
        self.tray.setToolTip(app.applicationName())
        if not IS_MAC:  # on macOS a context menu would hijack the click
            self.menu = QMenu()  # must live on self, or it gets garbage collected
            self.menu.addAction("Quit", app.quit)
            self.tray.setContextMenu(self.menu)
        self.tray.activated.connect(self.on_tray_activated)

        self.popover.add_requested.connect(self.open_dialog)
        self.popover.edit_requested.connect(self.edit_entry)
        self.popover.date_changed.connect(self.refresh)
        self.popover.quit_requested.connect(app.quit)

        self.refresh()
        self.tray.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self.popover.toggle_near(self.tray)

    def refresh(self):
        day = self.popover.selected_date().toString(Qt.ISODate)
        self.popover.set_entries(self.store.for_day(day))
        self.popover.mark_days(self.store.days_with_entries())

    def edit_entry(self, entry_id: int):
        entry = self.store.get(entry_id)
        if entry:
            self.open_dialog(QDate.fromString(entry.day, Qt.ISODate), entry)

    def open_dialog(self, date: QDate, entry: Entry = None):
        if self.dialog is not None:  # only one dialog at a time
            bring_to_front(self.dialog)
            return
        self.popover.hide()
        dlg = EntryDialog(date, entry)
        dlg.finished.connect(lambda code: self.on_dialog_finished(code, date, entry))
        self.dialog = dlg
        bring_to_front(dlg)

    def on_dialog_finished(self, code: int, date: QDate, entry: Entry):
        dlg, self.dialog = self.dialog, None
        if code == EntryDialog.SAVED:
            title, notes = dlg.values()
            if entry:
                self.store.update(entry.id, title, notes)
            else:
                self.store.add(date.toString(Qt.ISODate), title, notes)
        elif code == EntryDialog.DELETE and entry:
            self.store.delete(entry.id)
        self.refresh()
        QTimer.singleShot(0, dlg.deleteLater)  # never delete a dialog inside its own signal


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("TrayCalendar")
    app.setQuitOnLastWindowClosed(False)
    hide_dock_icon()

    if not QSystemTrayIcon.isSystemTrayAvailable():
        sys.exit("No system tray available.")

    tray_app = TrayApp(app)  # keep a reference for the lifetime of the app
    sys.exit(app.exec())


if __name__ == "__main__":
    main()