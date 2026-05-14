# NFL Schedule Builder - GUI Version
# Fixed: dropdown closes and stays closed after selecting a team

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

DEFAULT_SAVE_FILE = "nfl_schedule.json"
SETTINGS_FILE     = "nfl_scheduler_settings.json"

NFL_TEAMS = sorted([
    "Arizona Cardinals", "Atlanta Falcons", "Baltimore Ravens", "Buffalo Bills",
    "Carolina Panthers", "Chicago Bears", "Cincinnati Bengals", "Cleveland Browns",
    "Dallas Cowboys", "Denver Broncos", "Detroit Lions", "Green Bay Packers",
    "Houston Texans", "Indianapolis Colts", "Jacksonville Jaguars", "Kansas City Chiefs",
    "Las Vegas Raiders", "Los Angeles Chargers", "Los Angeles Rams", "Miami Dolphins",
    "Minnesota Vikings", "New England Patriots", "New Orleans Saints", "New York Giants",
    "New York Jets", "Philadelphia Eagles", "Pittsburgh Steelers", "San Francisco 49ers",
    "Seattle Seahawks", "Tampa Bay Buccaneers", "Tennessee Titans", "Washington Commanders"
])

BG_COLOR     = "#ffffff" # Main window background
PANEL_COLOR  = "#125740" # Panel/frame background (Schedule View panel)
ACCENT_COLOR = "#125740" # Column header background
HIGHLIGHT    = "#003F2D" # Title text, selected row, filter indicator
TEXT_COLOR   = "#eaeaea" # General text
BUTTON_COLOR = "#125740" # Button background color
BUTTON_TEXT  = "#ffffff" # Button text color
ENTRY_BG     = "#003F2D" # Search bar entry background
TREE_BG      = "#000000" # Treeview row background (even rows)
TREE_FG      = "#eaeaea" # Treeview row text color
TREE_SELECT  = "#003F2D" # Selected row highlight color
  
# ─────────────────────────────────────────────
# Settings Helpers
# ─────────────────────────────────────────────

def load_settings():
    """Load app settings. Returns dict with last_file and recent_files."""
    defaults = {"last_file": None, "recent_files": []}
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                data = json.load(f)
                defaults.update(data)
        except (json.JSONDecodeError, KeyError):
            pass
    return defaults


def save_settings(settings):
    """Persist app settings to JSON."""
    with open(SETTINGS_FILE, "w") as f:
        json.dump(settings, f, indent=4)


def record_recent_file(settings, filepath):
    """Add filepath to top of recent files list (max 5)."""
    recent = settings.get("recent_files", [])
    if filepath in recent:
        recent.remove(filepath)
    recent.insert(0, filepath)
    settings["recent_files"] = recent[:5]
    settings["last_file"]    = filepath


# ─────────────────────────────────────────────
# Startup Dialog
# ─────────────────────────────────────────────

class StartupDialog(tk.Toplevel):
    """
    Modal startup dialog shown before the main window opens.
    Lets the user resume the last file, pick a recent file,
    browse for a file, or start a new schedule.
    """

    def __init__(self, parent, settings):
        super().__init__(parent)
        self.title("NFL Schedule Builder — Open Schedule")
        self.resizable(False, False)
        self.configure(bg=BG_COLOR)
        self.grab_set()
        self.focus_set()

        self.chosen_file = None
        self.settings    = settings

        self._build_ui()

        self.update_idletasks()
        w  = self.winfo_width()
        h  = self.winfo_height()
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

        self.protocol("WM_DELETE_WINDOW", self._on_cancel)

    def _build_ui(self):
        """Build all dialog widgets."""

        # ── Header ──
        header = tk.Frame(self, bg=HIGHLIGHT)
        header.pack(fill="x")
        tk.Label(
            header,
            text="🏈  NFL Schedule Builder",
            font=("Helvetica", 20, "bold"),
            bg=HIGHLIGHT, fg=TEXT_COLOR, pady=16
        ).pack()

        body = tk.Frame(self, bg=BG_COLOR, padx=30, pady=20)
        body.pack(fill="both", expand=True)

        last_file    = self.settings.get("last_file")
        recent_files = self.settings.get("recent_files", [])

        # ── Resume last file ──
        if last_file and os.path.exists(last_file):
            tk.Label(
                body,
                text="Resume Last Session",
                font=("Helvetica", 12, "bold"),
                bg=BG_COLOR, fg=HIGHLIGHT
            ).pack(anchor="w", pady=(0, 6))

            try:
                mtime     = os.path.getmtime(last_file)
                mtime_str = datetime.fromtimestamp(mtime).strftime("%b %d, %Y  %I:%M %p")
            except OSError:
                mtime_str = "Unknown"

            resume_frame = tk.Frame(body, bg=PANEL_COLOR, padx=12, pady=10)
            resume_frame.pack(fill="x", pady=(0, 16))

            tk.Label(
                resume_frame,
                text=f"📄  {os.path.basename(last_file)}",
                font=("Helvetica", 11, "bold"),
                bg=PANEL_COLOR, fg=TEXT_COLOR, anchor="w"
            ).pack(fill="x")

            tk.Label(
                resume_frame,
                text=f"📁  {last_file}",
                font=("Helvetica", 9),
                bg=PANEL_COLOR, fg="#888888",
                anchor="w", wraplength=380
            ).pack(fill="x")

            tk.Label(
                resume_frame,
                text=f"🕐  Last modified: {mtime_str}",
                font=("Helvetica", 9, "italic"),
                bg=PANEL_COLOR, fg="#aaaaaa", anchor="w"
            ).pack(fill="x", pady=(4, 0))

            tk.Button(
                resume_frame,
                text="▶  Resume This File",
                command=lambda f=last_file: self._choose(f),
                font=("Helvetica", 11, "bold"),
                bg=HIGHLIGHT, fg=TEXT_COLOR,
                relief="flat", padx=10, pady=7, cursor="hand2",
                activebackground="#c73652", activeforeground=TEXT_COLOR
            ).pack(fill="x", pady=(10, 0))

        elif last_file and not os.path.exists(last_file):
            tk.Label(
                body,
                text=f"⚠️  Last file not found:\n{last_file}",
                font=("Helvetica", 9, "italic"),
                bg=BG_COLOR, fg="#e0a000",
                wraplength=380, justify="left"
            ).pack(anchor="w", pady=(0, 10))

        # ── Recent files ──
        other_recent = [
            f for f in recent_files
            if f != last_file and os.path.exists(f)
        ]

        if other_recent:
            tk.Label(
                body,
                text="Recent Files",
                font=("Helvetica", 12, "bold"),
                bg=BG_COLOR, fg=HIGHLIGHT
            ).pack(anchor="w", pady=(0, 6))

            recent_frame = tk.Frame(body, bg=PANEL_COLOR, padx=12, pady=8)
            recent_frame.pack(fill="x", pady=(0, 16))

            for filepath in other_recent:
                row = tk.Frame(recent_frame, bg=PANEL_COLOR)
                row.pack(fill="x", pady=2)

                tk.Label(
                    row,
                    text=f"📄  {os.path.basename(filepath)}",
                    font=("Helvetica", 10),
                    bg=PANEL_COLOR, fg=TEXT_COLOR,
                    anchor="w", width=28
                ).pack(side="left")

                tk.Label(
                    row,
                    text=filepath,
                    font=("Helvetica", 8),
                    bg=PANEL_COLOR, fg="#888888", anchor="w"
                ).pack(side="left", fill="x", expand=True, padx=(6, 10))

                tk.Button(
                    row,
                    text="Open",
                    command=lambda f=filepath: self._choose(f),
                    font=("Helvetica", 9, "bold"),
                    bg=BUTTON_COLOR, fg=TEXT_COLOR,
                    relief="flat", padx=8, pady=3, cursor="hand2",
                    activebackground=HIGHLIGHT, activeforeground=TEXT_COLOR
                ).pack(side="right")

        # ── Divider ──
        tk.Frame(body, bg=ACCENT_COLOR, height=1).pack(fill="x", pady=(0, 16))

        # ── Other options ──
        tk.Label(
            body,
            text="Other Options",
            font=("Helvetica", 12, "bold"),
            bg=BG_COLOR, fg=HIGHLIGHT
        ).pack(anchor="w", pady=(0, 8))

        options_frame = tk.Frame(body, bg=BG_COLOR)
        options_frame.pack(fill="x")

        tk.Button(
            options_frame,
            text="📂  Browse for Schedule File...",
            command=self._browse,
            font=("Helvetica", 11),
            bg=BUTTON_COLOR, fg=TEXT_COLOR,
            relief="flat", padx=10, pady=8, cursor="hand2",
            activebackground=HIGHLIGHT, activeforeground=TEXT_COLOR
        ).pack(fill="x", pady=3)

        tk.Button(
            options_frame,
            text="➕  Start a New Schedule",
            command=self._new,
            font=("Helvetica", 11),
            bg=ACCENT_COLOR, fg=TEXT_COLOR,
            relief="flat", padx=10, pady=8, cursor="hand2",
            activebackground=HIGHLIGHT, activeforeground=TEXT_COLOR
        ).pack(fill="x", pady=3)

    def _choose(self, filepath):
        self.chosen_file = filepath
        self.destroy()

    def _browse(self):
        path = filedialog.askopenfilename(
            parent=self,
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Open Schedule File"
        )
        if path:
            self.chosen_file = path
            self.destroy()

    def _new(self):
        self.chosen_file = "__NEW__"
        self.destroy()

    def _on_cancel(self):
        self._get_root_window().quit()

    def _get_root_window(self):
        widget = self
        while widget.master:
            widget = widget.master
        return widget


# ─────────────────────────────────────────────
# Searchable Combobox Widget
# ─────────────────────────────────────────────

class SearchableCombobox(tk.Frame):
    """
    A custom searchable combobox widget.
    Filters the dropdown list in real time as the user types.
    Closes and STAYS closed after a selection is made.
    """

    _all_instances = []

    def __init__(self, parent, values=None, placeholder="Type to search...",
                 bg=ENTRY_BG, fg=TEXT_COLOR, font=("Helvetica", 11), **kwargs):
        super().__init__(parent, bg=bg, **kwargs)

        self.all_values        = values or []
        self.placeholder       = placeholder
        self._dropdown_open    = False
        self._ignore_focus_out = False
        self._dropdown         = None
        self._listbox          = None

        # ── Key fix: lock flag to prevent dropdown reopening after selection ──
        # When True, _on_focus_in will not reopen the dropdown.
        # Reset to False after a short delay once selection is complete.
        self._just_selected    = False

        SearchableCombobox._all_instances.append(self)

        self.var = tk.StringVar()
        self.var.trace("w", self._on_type)

        self.entry = tk.Entry(
            self,
            textvariable=self.var,
            font=font,
            bg=bg, fg=fg,
            insertbackground=fg,
            relief="flat", bd=5
        )
        self.entry.pack(fill="x", ipady=4)

        self._show_placeholder()

        self.entry.bind("<FocusIn>",  self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Down>",     self._focus_listbox)
        self.entry.bind("<Return>",   self._on_entry_return)
        self.entry.bind("<Escape>",   lambda e: self._close_dropdown())

        self.after(100, self._bind_global_click)

    def _bind_global_click(self):
        """Bind a global click listener to detect outside clicks."""
        self.entry.bind_all("<ButtonPress-1>", self._on_global_click, add="+")

    def _get_root(self):
        """Walk up to find the root Tk window."""
        widget = self
        while widget.master:
            widget = widget.master
        return widget

    def _on_global_click(self, event):
        """Close dropdown if the click was outside this widget."""
        if not self._dropdown_open:
            return
        if event.widget == self.entry:
            return
        if self._listbox and event.widget == self._listbox:
            return
        if self._dropdown:
            try:
                x = self._dropdown.winfo_rootx()
                y = self._dropdown.winfo_rooty()
                w = self._dropdown.winfo_width()
                h = self._dropdown.winfo_height()
                if x <= event.x_root <= x + w and y <= event.y_root <= y + h:
                    return
            except tk.TclError:
                pass
        self._close_dropdown()
        if not self.var.get().strip() or self.var.get() == self.placeholder:
            self._show_placeholder()

    # ── Placeholder ──

    def _show_placeholder(self):
        """Show greyed placeholder text."""
        self.var.set(self.placeholder)
        self.entry.config(fg="#888888")
        self._has_placeholder = True

    def _clear_placeholder(self):
        """Remove placeholder on focus."""
        if getattr(self, "_has_placeholder", False):
            self.var.set("")
            self.entry.config(fg=TEXT_COLOR)
            self._has_placeholder = False

    def _on_focus_in(self, event):
        """
        Open dropdown on focus — but only if a selection was not
        just made. This prevents the dropdown from reopening
        immediately after the user clicks a list item.
        """
        # If we just completed a selection, skip reopening
        if self._just_selected:
            return

        self._clear_placeholder()
        self._close_all_others()
        self._open_dropdown(self.all_values)

    def _on_focus_out(self, event):
        """Fallback close for keyboard navigation."""
        if self._ignore_focus_out:
            return
        self.after(200, self._check_close_on_focus_out)

    def _check_close_on_focus_out(self):
        """Close if focus moved away via keyboard."""
        if self._ignore_focus_out:
            return
        try:
            focused = self._get_root().focus_get()
        except Exception:
            focused = None
        if focused == self._listbox or focused == self.entry:
            return
        self._close_dropdown()
        if not self.var.get().strip() or self.var.get() == self.placeholder:
            self._show_placeholder()

    def _close_all_others(self):
        """Close all other open SearchableCombobox dropdowns."""
        for instance in SearchableCombobox._all_instances:
            if instance is not self and instance._dropdown_open:
                instance._close_dropdown()

    # ── Typing Filter ──

    def _on_type(self, *args):
        """
        Filter the dropdown as the user types.
        Skips filtering if a selection was just made to prevent
        the dropdown from reopening with a filtered list.
        """
        if getattr(self, "_has_placeholder", False):
            return

        # Don't reopen the dropdown right after a selection
        if self._just_selected:
            return

        typed = self.var.get().strip().lower()
        if typed == self.placeholder.lower():
            return

        filtered = self.all_values if not typed else [
            t for t in self.all_values if typed in t.lower()
        ]
        self._open_dropdown(filtered)

    # ── Dropdown ──

    def _open_dropdown(self, options):
        """Open or refresh the floating dropdown listbox."""
        # Do not open if a selection was just made
        if self._just_selected:
            return

        if self._dropdown:
            self._dropdown.destroy()
            self._dropdown = None

        if not options:
            self._dropdown_open = False
            return

        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        w = self.entry.winfo_width()
        h = min(len(options), 8) * 28

        self._dropdown = tk.Toplevel(self)
        self._dropdown.wm_overrideredirect(True)
        self._dropdown.wm_geometry(f"{w}x{h}+{x}+{y}")
        self._dropdown.configure(bg=ENTRY_BG)
        self._dropdown.attributes("-topmost", True)

        scrollbar = tk.Scrollbar(self._dropdown, orient="vertical", bg=ACCENT_COLOR)
        scrollbar.pack(side="right", fill="y")

        self._listbox = tk.Listbox(
            self._dropdown,
            yscrollcommand=scrollbar.set,
            font=("Helvetica", 11),
            bg=ENTRY_BG, fg=TEXT_COLOR,
            selectbackground=HIGHLIGHT,
            selectforeground=TEXT_COLOR,
            relief="flat", bd=0,
            activestyle="dotbox",
            highlightthickness=1,
            highlightcolor=HIGHLIGHT
        )
        self._listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self._listbox.yview)

        for item in options:
            self._listbox.insert(tk.END, item)

        self._listbox.bind("<ButtonPress-1>", self._on_listbox_click)
        self._listbox.bind("<Return>",        self._on_listbox_return)
        self._listbox.bind("<Up>",            self._on_listbox_up)
        self._listbox.bind("<Escape>",        lambda e: self._close_dropdown())

        self._dropdown_open = True

    def _close_dropdown(self):
        """Destroy the dropdown and reset state."""
        if self._dropdown:
            try:
                self._dropdown.destroy()
            except tk.TclError:
                pass
            self._dropdown = None
        self._listbox       = None
        self._dropdown_open = False

    # ── Selection ──

    def _on_listbox_click(self, event):
        """Handle mouse click on a listbox item."""
        self._ignore_focus_out = True
        self.after(10, self._select_current)

    def _on_listbox_return(self, event):
        """Handle Enter on a listbox item."""
        self._select_current()

    def _select_current(self):
        """
        Set the entry to the selected listbox item and close the dropdown.
        Sets _just_selected = True to block the dropdown from reopening
        when focus returns to the entry after the listbox click.
        Resets _just_selected after a short delay.
        """
        if self._listbox:
            sel = self._listbox.curselection()
            if sel:
                value = self._listbox.get(sel[0])
                self._has_placeholder = False

                # ── Set lock BEFORE setting var to block _on_type ──
                self._just_selected = True

                self.var.set(value)
                self.entry.config(fg=TEXT_COLOR)

        # Close the dropdown
        self._close_dropdown()
        self._ignore_focus_out = False

        # Return focus to the entry (this triggers _on_focus_in,
        # but _just_selected=True will block it from reopening)
        self.entry.focus_set()

        # ── Reset the lock after a short delay ──
        # 300ms is enough for all the focus/click events to settle
        self.after(300, self._clear_just_selected)

    def _clear_just_selected(self):
        """Release the post-selection lock so dropdown can open again on next focus."""
        self._just_selected = False

    def _on_entry_return(self, event):
        """Auto-select if only one match remains on Enter."""
        typed = self.var.get().strip().lower()
        matches = [t for t in self.all_values if typed in t.lower()]
        if len(matches) == 1:
            # Set lock before setting value
            self._just_selected = True
            self.var.set(matches[0])
            self.entry.config(fg=TEXT_COLOR)
            self._has_placeholder = False
            self._close_dropdown()
            self.after(300, self._clear_just_selected)

    def _focus_listbox(self, event):
        """Move focus into the listbox on Down arrow."""
        if self._listbox:
            self._listbox.focus_set()
            self._listbox.selection_set(0)

    def _on_listbox_up(self, event):
        """Return focus to entry when pressing Up at top of list."""
        if self._listbox and self._listbox.curselection():
            if self._listbox.curselection()[0] == 0:
                self.entry.focus_set()

    # ── Public Methods ──

    def get(self):
        """Return current value, or empty string if placeholder shown."""
        if getattr(self, "_has_placeholder", False):
            return ""
        val = self.var.get().strip()
        if val == self.placeholder:
            return ""
        return val

    def set(self, value):
        """Programmatically set the combobox value."""
        # Lock to prevent _on_type from reopening the dropdown
        self._just_selected    = True
        self._has_placeholder  = False
        self.var.set(value)
        self.entry.config(fg=TEXT_COLOR)
        self._close_dropdown()
        self.after(300, self._clear_just_selected)

    def clear(self):
        """Clear entry and restore placeholder."""
        self._close_dropdown()
        self._just_selected = False
        self._show_placeholder()

    def update_values(self, new_values):
        """Replace the full list of selectable options."""
        self.all_values = new_values


# ─────────────────────────────────────────────
# File I/O
# ─────────────────────────────────────────────

def load_games(filepath):
    """Load games from a JSON file. Returns a list of game dicts."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                return data.get("games", [])
        except (json.JSONDecodeError, KeyError):
            messagebox.showwarning(
                "Load Warning", f"Could not read '{filepath}'. Starting fresh."
            )
            return []
    return []


def save_games(filepath, games):
    """Save games list to JSON with metadata header."""
    data = {
        "meta": {
            "app": "NFL Schedule Builder",
            "last_saved": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        "games": games
    }
    with open(filepath, "w") as f:
        json.dump(data, f, indent=4)


# ─────────────────────────────────────────────
# Sort Key Helper
# ─────────────────────────────────────────────

def _sort_key(game, col_key):
    """Numeric sort for week/year, string sort for everything else."""
    val = game.get(col_key, "")
    if col_key in ("week", "year"):
        try:
            return (0, int(val))
        except (ValueError, TypeError):
            return (1, str(val).lower())
    return (0, str(val).lower())


# ─────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────

class NFLSchedulerApp:
    def __init__(self, root, initial_file, settings):
        """
        Initialize the main application.
        :param root: Root Tk window
        :param initial_file: File path chosen at startup, or None for new
        :param settings: Loaded settings dict
        """
        self.root     = root
        self.settings = settings

        self.root.title("🏈 NFL Schedule Builder")
        self.root.geometry("1280x780")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(True, True)

        self._sorted_indices = None
        self._sort_col       = None
        self._sort_ascending = {}

        if initial_file:
            self.save_file = initial_file
            self.games     = load_games(self.save_file)
        else:
            self.save_file = DEFAULT_SAVE_FILE
            self.games     = []

        self._build_menu()
        self._build_header()
        self._build_main_layout()
        self._build_status_bar()

        self.refresh_schedule_view()
        self.refresh_filter_options()
        self.update_status(
            f"Loaded {len(self.games)} game(s) from '{self.save_file}'"
            if initial_file else "New schedule started."
        )

        if initial_file:
            record_recent_file(self.settings, self.save_file)
            save_settings(self.settings)

    # ─────────────────────────────────────────
    # Menu Bar
    # ─────────────────────────────────────────

    def _build_menu(self):
        menubar = tk.Menu(self.root, bg=ACCENT_COLOR, fg=TEXT_COLOR, tearoff=0)

        file_menu = tk.Menu(menubar, tearoff=0, bg=PANEL_COLOR, fg=TEXT_COLOR)
        file_menu.add_command(label="New Schedule",      command=self.new_schedule)
        file_menu.add_command(label="Open Schedule...",  command=self.open_schedule)
        file_menu.add_command(label="Save",              command=self.save_now)
        file_menu.add_command(label="Save As...",        command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Export to CSV",     command=self.export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit",              command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg=PANEL_COLOR, fg=TEXT_COLOR)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    # ─────────────────────────────────────────
    # Header
    # ─────────────────────────────────────────

    def _build_header(self):
        header = tk.Frame(self.root, bg=HIGHLIGHT, height=55)
        header.pack(fill="x", side="top")

        tk.Label(
            header,
            text="🏈  NFL Schedule Builder",
            font=("Helvetica", 22, "bold"),
            bg=HIGHLIGHT, fg=TEXT_COLOR
        ).pack(side="left", padx=20, pady=10)

        self.file_label = tk.Label(
            header,
            text=f"File: {self.save_file}",
            font=("Helvetica", 10),
            bg=HIGHLIGHT, fg=TEXT_COLOR
        )
        self.file_label.pack(side="right", padx=20)

    # ─────────────────────────────────────────
    # Main Layout
    # ─────────────────────────────────────────

    def _build_main_layout(self):
        main_frame = tk.Frame(self.root, bg=BG_COLOR)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left = tk.Frame(main_frame, bg=PANEL_COLOR, width=320, relief="flat", bd=2)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)
        self._build_form(left)

        right = tk.Frame(main_frame, bg=PANEL_COLOR, relief="flat", bd=2)
        right.pack(side="left", fill="both", expand=True)
        self._build_schedule_view(right)

    # ─────────────────────────────────────────
    # Left Panel: Game Entry Form
    # ─────────────────────────────────────────

    def _build_form(self, parent):
        tk.Label(
            parent,
            text="Add / Edit Game",
            font=("Helvetica", 14, "bold"),
            bg=PANEL_COLOR, fg=HIGHLIGHT
        ).pack(pady=(15, 5))

        tk.Frame(parent, bg=HIGHLIGHT, height=2).pack(fill="x", padx=15, pady=(0, 10))

        form = tk.Frame(parent, bg=PANEL_COLOR)
        form.pack(fill="x", padx=15)

        def label(text):
            tk.Label(
                form, text=text,
                font=("Helvetica", 10, "bold"),
                bg=PANEL_COLOR, fg=TEXT_COLOR, anchor="w"
            ).pack(fill="x", pady=(8, 1))

        def entry(default=""):
            e = tk.Entry(
                form,
                font=("Helvetica", 11),
                bg=ENTRY_BG, fg=TEXT_COLOR,
                insertbackground=TEXT_COLOR,
                relief="flat", bd=5
            )
            e.pack(fill="x", ipady=4)
            if default:
                e.insert(0, default)
            return e

        label("Week #")
        self.week_entry = entry()

        label("Date (MM/DD/YYYY or TBD)")
        self.date_entry = entry("TBD")

        label("Away Team")
        self.away_combo = SearchableCombobox(form, values=NFL_TEAMS)
        self.away_combo.pack(fill="x")

        label("Home Team")
        self.home_combo = SearchableCombobox(form, values=NFL_TEAMS)
        self.home_combo.pack(fill="x")

        label("Game Time (e.g. 1:00 PM ET)")
        self.time_entry = entry("TBD")

        label("Location / Stadium")
        self.location_entry = entry("TBD")

        label("Season Year")
        self.year_entry = entry(str(datetime.now().year))

        tk.Frame(parent, bg=HIGHLIGHT, height=2).pack(fill="x", padx=15, pady=15)

        btn_frame = tk.Frame(parent, bg=PANEL_COLOR)
        btn_frame.pack(fill="x", padx=15)

        def styled_btn(text, cmd, color=BUTTON_COLOR):
            return tk.Button(
                btn_frame, text=text, command=cmd,
                font=("Helvetica", 11, "bold"),
                bg=color, fg=BUTTON_TEXT,
                relief="flat", bd=0,
                padx=10, pady=8, cursor="hand2",
                activebackground=HIGHLIGHT,
                activeforeground=TEXT_COLOR
            )

        styled_btn("➕  Add Game",    self.add_game,    HIGHLIGHT).pack(fill="x", pady=3)
        styled_btn("✏️  Update Game", self.update_game, BUTTON_COLOR).pack(fill="x", pady=3)
        styled_btn("🔄  Clear Form",  self.clear_form,  ACCENT_COLOR).pack(fill="x", pady=3)
        styled_btn("🗑️  Delete Game", self.delete_game, "#8b0000").pack(fill="x", pady=3)

    # ─────────────────────────────────────────
    # Right Panel: Schedule View
    # ─────────────────────────────────────────

    def _build_schedule_view(self, parent):
        filter_frame = tk.Frame(parent, bg=PANEL_COLOR)
        filter_frame.pack(fill="x", padx=10, pady=(10, 2))

        tk.Label(
            filter_frame,
            text="Schedule View",
            font=("Helvetica", 14, "bold"),
            bg=PANEL_COLOR, fg=HIGHLIGHT
        ).grid(row=0, column=0, sticky="w", padx=(0, 15))

        tk.Label(
            filter_frame, text="Team:",
            font=("Helvetica", 10, "bold"),
            bg=PANEL_COLOR, fg=TEXT_COLOR
        ).grid(row=0, column=1, sticky="w", padx=(0, 4))

        self.filter_team_combo = SearchableCombobox(
            filter_frame,
            values=["All Teams"] + NFL_TEAMS,
            placeholder="All Teams",
            font=("Helvetica", 10)
        )
        self.filter_team_combo.grid(row=0, column=2, sticky="w", padx=(0, 4))
        self.filter_team_combo.entry.bind(
            "<Return>", lambda e: self.refresh_schedule_view()
        )

        tk.Label(
            filter_frame, text="Week:",
            font=("Helvetica", 10, "bold"),
            bg=PANEL_COLOR, fg=TEXT_COLOR
        ).grid(row=0, column=3, sticky="w", padx=(10, 4))

        self.filter_week_combo = SearchableCombobox(
            filter_frame,
            values=["All Weeks"] + [str(w) for w in range(1, 24)],
            placeholder="All Weeks",
            font=("Helvetica", 10)
        )
        self.filter_week_combo.grid(row=0, column=4, sticky="w", padx=(0, 4))
        self.filter_week_combo.entry.bind(
            "<Return>", lambda e: self.refresh_schedule_view()
        )

        tk.Button(
            filter_frame, text="Apply",
            command=self.refresh_schedule_view,
            font=("Helvetica", 9, "bold"),
            bg=HIGHLIGHT, fg=TEXT_COLOR,
            relief="flat", padx=8, pady=3, cursor="hand2"
        ).grid(row=0, column=5, padx=(6, 2))

        tk.Button(
            filter_frame, text="Clear",
            command=self._clear_filters,
            font=("Helvetica", 9),
            bg=ACCENT_COLOR, fg=TEXT_COLOR,
            relief="flat", padx=8, pady=3, cursor="hand2"
        ).grid(row=0, column=6, padx=(2, 10))

        search_frame = tk.Frame(parent, bg=PANEL_COLOR)
        search_frame.pack(fill="x", padx=10, pady=(2, 6))

        tk.Label(
            search_frame, text="🔍 Search:",
            font=("Helvetica", 10, "bold"),
            bg=PANEL_COLOR, fg=TEXT_COLOR
        ).pack(side="left", padx=(0, 6))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self.refresh_schedule_view())

        tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Helvetica", 10),
            bg=ENTRY_BG, fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat", bd=4, width=30
        ).pack(side="left")

        self.filter_status_label = tk.Label(
            search_frame, text="",
            font=("Helvetica", 9, "italic"),
            bg=PANEL_COLOR, fg=HIGHLIGHT
        )
        self.filter_status_label.pack(side="left", padx=(15, 0))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "NFL.Treeview",
            background=TREE_BG, foreground=TREE_FG,
            fieldbackground=TREE_BG, rowheight=28,
            font=("Helvetica", 10)
        )
        style.configure(
            "NFL.Treeview.Heading",
            background=ACCENT_COLOR, foreground=TEXT_COLOR,
            font=("Helvetica", 10, "bold"), relief="flat"
        )
        style.map(
            "NFL.Treeview",
            background=[("selected", TREE_SELECT)],
            foreground=[("selected", TEXT_COLOR)]
        )

        columns = ("week", "date", "away", "home", "time", "location", "year")

        tree_frame = tk.Frame(parent, bg=PANEL_COLOR)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 5))

        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="NFL.Treeview",
            selectmode="browse"
        )

        self._col_headings = {
            "week":     "Week",
            "date":     "Date",
            "away":     "Away Team",
            "home":     "Home Team",
            "time":     "Time",
            "location": "Location",
            "year":     "Season"
        }
        col_widths = {
            "week": 55, "date": 170, "away": 175,
            "home": 175, "time": 110, "location": 170, "year": 65
        }
        for col in columns:
            self.tree.heading(
                col,
                text=self._col_headings[col],
                command=lambda c=col: self.sort_tree(c)
            )
            self.tree.column(col, width=col_widths[col], anchor="center")

        vsb = ttk.Scrollbar(tree_frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        self.count_label = tk.Label(
            parent, text="",
            font=("Helvetica", 9, "italic"),
            bg=PANEL_COLOR, fg=TEXT_COLOR
        )
        self.count_label.pack(anchor="e", padx=15, pady=(0, 5))

    # ─────────────────────────────────────────
    # Status Bar
    # ─────────────────────────────────────────

    def _build_status_bar(self):
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Helvetica", 9),
            bg=ACCENT_COLOR, fg=TEXT_COLOR,
            anchor="w", padx=10
        ).pack(fill="x", side="bottom")

    # ─────────────────────────────────────────
    # Core Game Functions
    # ─────────────────────────────────────────

    def add_game(self):
        game = self._get_form_data()
        if game is None:
            return
        for g in self.games:
            if (g["week"]      == game["week"] and
                g["home_team"] == game["home_team"] and
                g["away_team"] == game["away_team"] and
                g["year"]      == game["year"]):
                messagebox.showwarning("Duplicate Game", "This game already exists.")
                return
        self.games.append(game)
        self._sorted_indices = None
        self._reset_column_headings()
        self._save_and_refresh(
            f"Added: Week {game['week']} | {game['away_team']} @ {game['home_team']}"
        )
        self.clear_form()

    def update_game(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Click a game to select it first.")
            return
        game = self._get_form_data()
        if game is None:
            return
        idx = int(self.tree.item(selected[0], "tags")[0])
        self.games[idx] = game
        self._save_and_refresh(
            f"Updated: Week {game['week']} | {game['away_team']} @ {game['home_team']}"
        )

    def delete_game(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Click a game to select it first.")
            return
        idx = int(self.tree.item(selected[0], "tags")[0])
        g = self.games[idx]
        if messagebox.askyesno(
            "Confirm Delete",
            f"Delete Week {g['week']} | {g['away_team']} @ {g['home_team']}?"
        ):
            self.games.pop(idx)
            if self._sorted_indices is not None:
                self._sorted_indices = [
                    i if i < idx else i - 1
                    for i in self._sorted_indices if i != idx
                ]
            self._save_and_refresh(
                f"Deleted: Week {g['week']} | {g['away_team']} @ {g['home_team']}"
            )
            self.clear_form()

    def _get_form_data(self):
        week_str = self.week_entry.get().strip()
        if not week_str.isdigit() or not (1 <= int(week_str) <= 23):
            messagebox.showerror("Invalid Week", "Week must be a number between 1 and 23.")
            return None

        away = self.away_combo.get()
        home = self.home_combo.get()
        if not away or not home:
            messagebox.showerror("Missing Teams", "Please select both home and away teams.")
            return None
        if away not in NFL_TEAMS or home not in NFL_TEAMS:
            messagebox.showerror("Invalid Team", "Please select a valid NFL team.")
            return None
        if away == home:
            messagebox.showerror("Same Team", "Home and Away teams cannot be the same.")
            return None

        date_str = self.date_entry.get().strip()
        if date_str.upper() != "TBD":
            try:
                date_str = datetime.strptime(date_str, "%m/%d/%Y").strftime("%m/%d/%Y")
            except ValueError:
                messagebox.showerror("Invalid Date", "Date must be MM/DD/YYYY or 'TBD'.")
                return None

        year_str = self.year_entry.get().strip()
        if not year_str.isdigit():
            messagebox.showerror("Invalid Year", "Please enter a valid 4-digit year.")
            return None

        return {
            "week":      int(week_str),
            "date":      date_str,
            "away_team": away,
            "home_team": home,
            "time":      self.time_entry.get().strip() or "TBD",
            "location":  self.location_entry.get().strip() or "TBD",
            "year":      int(year_str)
        }

    def clear_form(self):
        self.week_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END);     self.date_entry.insert(0, "TBD")
        self.away_combo.clear()
        self.home_combo.clear()
        self.time_entry.delete(0, tk.END);     self.time_entry.insert(0, "TBD")
        self.location_entry.delete(0, tk.END); self.location_entry.insert(0, "TBD")
        self.year_entry.delete(0, tk.END);     self.year_entry.insert(0, str(datetime.now().year))
        self.tree.selection_remove(self.tree.selection())

    def on_row_select(self, event):
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(self.tree.item(selected[0], "tags")[0])
        g = self.games[idx]
        self.week_entry.delete(0, tk.END);     self.week_entry.insert(0, str(g["week"]))
        self.date_entry.delete(0, tk.END);     self.date_entry.insert(0, g["date"])
        self.away_combo.set(g["away_team"])
        self.home_combo.set(g["home_team"])
        self.time_entry.delete(0, tk.END);     self.time_entry.insert(0, g["time"])
        self.location_entry.delete(0, tk.END); self.location_entry.insert(0, g["location"])
        self.year_entry.delete(0, tk.END);     self.year_entry.insert(0, str(g["year"]))

    # ─────────────────────────────────────────
    # Schedule View
    # ─────────────────────────────────────────

    def refresh_schedule_view(self):
        """Refresh the treeview with current filters applied."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        team_filter = self.filter_team_combo.get()
        if not team_filter or team_filter == "All Teams":
            team_filter = None

        week_filter = self.filter_week_combo.get()
        if not week_filter or week_filter == "All Weeks":
            week_filter = None
        else:
            week_filter = week_filter.replace("Week", "").strip()
            if not week_filter.isdigit():
                week_filter = None

        search_term = self.search_var.get().strip().lower()

        active_filters = []
        if team_filter:  active_filters.append(f"Team: {team_filter}")
        if week_filter:  active_filters.append(f"Week: {week_filter}")
        if search_term:  active_filters.append(f'Search: "{search_term}"')
        self.filter_status_label.config(
            text=("Filters: " + "  |  ".join(active_filters)) if active_filters else ""
        )

        ordered_indices = (
            self._sorted_indices
            if self._sorted_indices is not None
            else list(range(len(self.games)))
        )

        visible = 0
        for idx in ordered_indices:
            g = self.games[idx]

            if team_filter:
                if g["home_team"] != team_filter and g["away_team"] != team_filter:
                    continue
            if week_filter:
                if int(g["week"]) != int(week_filter):
                    continue
            if search_term:
                if search_term not in " ".join(str(v).lower() for v in g.values()):
                    continue

            tag = "even" if visible % 2 == 0 else "odd"
            self.tree.insert(
                "", "end",
                values=(
                    g["week"], g["date"], g["away_team"],
                    g["home_team"], g["time"], g["location"],
                    g.get("year", "N/A")
                ),
                tags=(str(idx), tag)
            )
            visible += 1

        self.tree.tag_configure("even", background=TREE_BG)
        self.tree.tag_configure("odd",  background="#111122")
        self.count_label.config(text=f"Showing {visible} of {len(self.games)} game(s)")

    def _clear_filters(self):
        self.filter_team_combo.clear()
        self.filter_week_combo.clear()
        self.search_var.set("")
        self.refresh_schedule_view()
        self.update_status("Filters cleared.")

    def refresh_filter_options(self):
        teams = set()
        for g in self.games:
            teams.add(g["home_team"])
            teams.add(g["away_team"])
        self.filter_team_combo.update_values(["All Teams"] + sorted(teams))
        weeks = sorted(set(g["week"] for g in self.games), key=lambda w: int(w))
        self.filter_week_combo.update_values(
            ["All Weeks"] + [str(w) for w in weeks]
        )

    def sort_tree(self, col):
        col_map = {
            "week": "week", "date": "date", "away": "away_team",
            "home": "home_team", "time": "time",
            "location": "location", "year": "year"
        }
        key       = col_map.get(col, col)
        ascending = self._sort_ascending.get(col, True)
        self._sort_ascending[col] = not ascending

        self._sorted_indices = sorted(
            range(len(self.games)),
            key=lambda i: _sort_key(self.games[i], key),
            reverse=not ascending
        )
        self._sort_col = col

        for c, label in self._col_headings.items():
            arrow = (" ▲" if ascending else " ▼") if c == col else ""
            self.tree.heading(c, text=label + arrow)

        self.refresh_schedule_view()
        self.update_status(
            f"Sorted by {col} ({'ascending' if ascending else 'descending'})"
        )

    def _reset_column_headings(self):
        for c, label in self._col_headings.items():
            self.tree.heading(c, text=label)
        self._sort_col = None

    # ─────────────────────────────────────────
    # File Operations
    # ─────────────────────────────────────────

    def _save_and_refresh(self, msg=""):
        save_games(self.save_file, self.games)
        self.refresh_schedule_view()
        self.refresh_filter_options()
        self.update_status(msg + f" | Saved to '{self.save_file}'")

    def _update_recent_and_save_settings(self):
        record_recent_file(self.settings, self.save_file)
        save_settings(self.settings)
        self.file_label.config(text=f"File: {self.save_file}")

    def save_now(self):
        save_games(self.save_file, self.games)
        self._update_recent_and_save_settings()
        self.update_status(f"Saved {len(self.games)} game(s) to '{self.save_file}'")

    def save_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Save Schedule As"
        )
        if path:
            self.save_file = path
            save_games(self.save_file, self.games)
            self._update_recent_and_save_settings()
            self.update_status(f"Saved to '{self.save_file}'")

    def open_schedule(self):
        path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Open Schedule File"
        )
        if path:
            self.save_file       = path
            self.games           = load_games(self.save_file)
            self._sorted_indices = None
            self._reset_column_headings()
            self._update_recent_and_save_settings()
            self.refresh_schedule_view()
            self.refresh_filter_options()
            self.update_status(
                f"Opened '{self.save_file}' | {len(self.games)} game(s) loaded"
            )

    def new_schedule(self):
        if messagebox.askyesno("New Schedule",
                               "Start a new schedule? Unsaved changes will be lost."):
            path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
                title="Save New Schedule As"
            )
            if not path:
                return
            self.games           = []
            self.save_file       = path
            self._sorted_indices = None
            self._reset_column_headings()
            save_games(self.save_file, self.games)
            self._update_recent_and_save_settings()
            self.refresh_schedule_view()
            self.refresh_filter_options()
            self.clear_form()
            self.update_status(f"New schedule started: '{self.save_file}'")

    def export_csv(self):
        if not self.games:
            messagebox.showinfo("Empty", "No games to export.")
            return
        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Export to CSV"
        )
        if path:
            import csv
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["year","week","date","away_team","home_team","time","location"]
                )
                writer.writeheader()
                ordered = (
                    [self.games[i] for i in self._sorted_indices]
                    if self._sorted_indices is not None
                    else self.games
                )
                for g in ordered:
                    writer.writerow(g)
            self.update_status(f"Exported {len(self.games)} game(s) to '{path}'")

    def update_status(self, msg):
        self.status_var.set(f"  {msg}")

    def show_about(self):
        messagebox.showinfo(
            "About NFL Schedule Builder",
            "🏈 NFL Schedule Builder\n\n"
            "Build your NFL season schedule with ease.\n\n"
            "Features:\n"
            "  • Startup dialog with recent files\n"
            "  • Searchable team dropdowns\n"
            "  • Dropdown closes after selection\n"
            "  • Filter by team AND week\n"
            "  • Click outside to close dropdowns\n"
            "  • Numeric week & year sorting\n"
            "  • Toggle ascending/descending sort\n"
            "  • Default view: insertion order\n"
            "  • Filters work independently of sort\n"
            "  • Live search across all fields\n"
            "  • Add, edit, delete games\n"
            "  • Auto-save to JSON\n"
            "  • Export to CSV"
        )


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    root.withdraw()

    settings = load_settings()

    dialog = StartupDialog(root, settings)
    root.wait_window(dialog)

    chosen = dialog.chosen_file

    if chosen == "__NEW__":
        new_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Save New Schedule As"
        )
        if not new_path:
            root.quit()
        else:
            save_games(new_path, [])
            initial_file = new_path
    else:
        initial_file = chosen

    if initial_file:
        root.deiconify()
        app = NFLSchedulerApp(root, initial_file, settings)
        root.mainloop()