# NFL Schedule Builder - GUI Version with Searchable Team Dropdowns
# Uses Tkinter for the interface and JSON for persistent file storage
# Features a custom autocomplete combobox for team selection

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

DEFAULT_SAVE_FILE = "nfl_schedule.json"  # Default storage file

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

# Color theme
BG_COLOR    = "#1a1a2e"
PANEL_COLOR = "#16213e"
ACCENT_COLOR = "#0f3460"
HIGHLIGHT   = "#e94560"
TEXT_COLOR  = "#eaeaea"
BUTTON_COLOR = "#0f3460"
BUTTON_TEXT = "#ffffff"
ENTRY_BG    = "#0d0d1a"
TREE_BG     = "#0d0d1a"
TREE_FG     = "#eaeaea"
TREE_SELECT = "#e94560"

# ─────────────────────────────────────────────
# Searchable Combobox Widget
# ─────────────────────────────────────────────

class SearchableCombobox(tk.Frame):
    """
    A custom searchable combobox widget.
    Shows a dropdown list that filters in real time as the user types.
    """

    def __init__(self, parent, values=None, placeholder="Type to search...",
                 bg=ENTRY_BG, fg=TEXT_COLOR, font=("Helvetica", 11), **kwargs):
        """
        Initialize the searchable combobox.
        :param parent: Parent widget
        :param values: List of string options
        :param placeholder: Placeholder text shown when empty
        """
        super().__init__(parent, bg=bg, **kwargs)

        self.all_values = values or []        # Full list of options
        self.placeholder = placeholder
        self._dropdown_open = False           # Track if dropdown is visible
        self._ignore_focus_out = False        # Prevent closing on internal clicks

        # ── Entry field ──
        self.var = tk.StringVar()
        self.var.trace("w", self._on_type)   # Trigger filter on every keystroke

        self.entry = tk.Entry(
            self,
            textvariable=self.var,
            font=font,
            bg=bg,
            fg=fg,
            insertbackground=fg,
            relief="flat",
            bd=5
        )
        self.entry.pack(fill="x", ipady=4)

        # Show placeholder text initially
        self._show_placeholder()

        # ── Bind events ──
        self.entry.bind("<FocusIn>",  self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Down>",     self._focus_listbox)   # Arrow down moves to list
        self.entry.bind("<Return>",   self._on_entry_return)
        self.entry.bind("<Escape>",   lambda e: self._close_dropdown())

        # ── Dropdown toplevel window (hidden initially) ──
        self._dropdown = None
        self._listbox  = None

    # ── Placeholder Helpers ──

    def _show_placeholder(self):
        """Insert placeholder text in grey."""
        self.entry.config(fg="#888888")
        self.entry.insert(0, self.placeholder)
        self._has_placeholder = True

    def _clear_placeholder(self):
        """Remove placeholder text when user focuses the field."""
        if getattr(self, "_has_placeholder", False):
            self.entry.config(fg=TEXT_COLOR)
            self.entry.delete(0, tk.END)
            self._has_placeholder = False

    def _on_focus_in(self, event):
        """Clear placeholder on focus."""
        self._clear_placeholder()
        self._open_dropdown(self.all_values)

    def _on_focus_out(self, event):
        """Close dropdown when focus leaves, unless clicking inside the list."""
        if self._ignore_focus_out:
            return
        # Small delay so listbox click registers before closing
        self.after(150, self._check_close)

    def _check_close(self):
        """Close dropdown if focus is no longer in the widget."""
        if not self._ignore_focus_out:
            self._close_dropdown()
            # Restore placeholder if empty
            if not self.var.get().strip():
                self._show_placeholder()

    # ── Typing Filter ──

    def _on_type(self, *args):
        """Filter dropdown list as user types."""
        if getattr(self, "_has_placeholder", False):
            return

        typed = self.var.get().strip().lower()

        if typed == "":
            # Show all options if field is empty
            filtered = self.all_values
        else:
            # Filter: show teams whose name contains the typed string
            filtered = [t for t in self.all_values if typed in t.lower()]

        self._open_dropdown(filtered)

    # ── Dropdown Open/Close ──

    def _open_dropdown(self, options):
        """
        Open (or refresh) the dropdown listbox below the entry.
        :param options: Filtered list of strings to display
        """
        # Destroy old dropdown if it exists
        if self._dropdown:
            self._dropdown.destroy()
            self._dropdown = None

        if not options:
            return  # Nothing to show

        # Get position of the entry widget on screen
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        w = self.entry.winfo_width()

        # Create a floating Toplevel window for the dropdown
        self._dropdown = tk.Toplevel(self)
        self._dropdown.wm_overrideredirect(True)  # No window border/title bar
        self._dropdown.wm_geometry(f"{w}x{min(len(options), 8) * 28}+{x}+{y}")
        self._dropdown.configure(bg=ENTRY_BG)
        self._dropdown.attributes("-topmost", True)  # Always on top

        # Scrollbar for long lists
        scrollbar = tk.Scrollbar(self._dropdown, orient="vertical", bg=ACCENT_COLOR)
        scrollbar.pack(side="right", fill="y")

        # Listbox of matching options
        self._listbox = tk.Listbox(
            self._dropdown,
            yscrollcommand=scrollbar.set,
            font=("Helvetica", 11),
            bg=ENTRY_BG,
            fg=TEXT_COLOR,
            selectbackground=HIGHLIGHT,
            selectforeground=TEXT_COLOR,
            relief="flat",
            bd=0,
            activestyle="dotbox",
            highlightthickness=1,
            highlightcolor=HIGHLIGHT
        )
        self._listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self._listbox.yview)

        # Insert filtered options
        for item in options:
            self._listbox.insert(tk.END, item)

        # Bind listbox selection events
        self._listbox.bind("<ButtonPress-1>", self._on_listbox_click)
        self._listbox.bind("<Return>",        self._on_listbox_return)
        self._listbox.bind("<Up>",            self._on_listbox_up)
        self._listbox.bind("<Escape>",        lambda e: self._close_dropdown())

        # Mark flag so focus-out doesn't immediately close
        self._dropdown_open = True

    def _close_dropdown(self):
        """Destroy the dropdown window."""
        if self._dropdown:
            self._dropdown.destroy()
            self._dropdown = None
        self._dropdown_open = False

    # ── Selection Events ──

    def _on_listbox_click(self, event):
        """Handle mouse click on a listbox item."""
        self._ignore_focus_out = True
        self.after(10, self._select_current)

    def _on_listbox_return(self, event):
        """Handle Enter key press on a listbox item."""
        self._select_current()

    def _select_current(self):
        """Set the entry value to the selected listbox item."""
        if self._listbox:
            selection = self._listbox.curselection()
            if selection:
                value = self._listbox.get(selection[0])
                self._has_placeholder = False
                self.var.set(value)
                self.entry.config(fg=TEXT_COLOR)
        self._close_dropdown()
        self._ignore_focus_out = False
        self.entry.focus_set()

    def _on_entry_return(self, event):
        """If only one match, auto-select it on Enter."""
        typed = self.var.get().strip().lower()
        matches = [t for t in self.all_values if typed in t.lower()]
        if len(matches) == 1:
            self.var.set(matches[0])
            self._close_dropdown()

    def _focus_listbox(self, event):
        """Move focus from entry to listbox on Down arrow key."""
        if self._listbox:
            self._listbox.focus_set()
            self._listbox.selection_set(0)

    def _on_listbox_up(self, event):
        """Move focus back to entry if at top of listbox."""
        if self._listbox:
            if self._listbox.curselection() and self._listbox.curselection()[0] == 0:
                self.entry.focus_set()

    # ── Public Methods ──

    def get(self):
        """Return the current value (empty string if placeholder shown)."""
        if getattr(self, "_has_placeholder", False):
            return ""
        return self.var.get().strip()

    def set(self, value):
        """Programmatically set the entry value."""
        self._has_placeholder = False
        self.var.set(value)
        self.entry.config(fg=TEXT_COLOR)
        self._close_dropdown()

    def clear(self):
        """Clear the entry and restore placeholder."""
        self.var.set("")
        self._show_placeholder()
        self._close_dropdown()


# ─────────────────────────────────────────────
# File I/O Functions
# ─────────────────────────────────────────────

def load_games(filepath):
    """Load games from a JSON file. Returns a list of game dicts."""
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                return data.get("games", [])
        except (json.JSONDecodeError, KeyError):
            messagebox.showwarning("Load Warning", f"Could not read '{filepath}'. Starting fresh.")
            return []
    return []


def save_games(filepath, games):
    """Save games list to a JSON file with metadata."""
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
# Main Application Class
# ─────────────────────────────────────────────

class NFLSchedulerApp:
    def __init__(self, root):
        """Initialize the main application window."""
        self.root = root
        self.root.title("🏈 NFL Schedule Builder")
        self.root.geometry("1200x750")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(True, True)

        self.save_file = DEFAULT_SAVE_FILE
        self.games = load_games(self.save_file)

        self._build_menu()
        self._build_header()
        self._build_main_layout()
        self._build_status_bar()

        self.refresh_schedule_view()
        self.refresh_team_filter()
        self.update_status(f"Loaded {len(self.games)} game(s) from '{self.save_file}'")

    # ─────────────────────────────────────────
    # Menu Bar
    # ─────────────────────────────────────────

    def _build_menu(self):
        """Build the top menu bar."""
        menubar = tk.Menu(self.root, bg=ACCENT_COLOR, fg=TEXT_COLOR, tearoff=0)

        file_menu = tk.Menu(menubar, tearoff=0, bg=PANEL_COLOR, fg=TEXT_COLOR)
        file_menu.add_command(label="New Schedule",     command=self.new_schedule)
        file_menu.add_command(label="Open Schedule...", command=self.open_schedule)
        file_menu.add_command(label="Save",             command=self.save_now)
        file_menu.add_command(label="Save As...",       command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Export to CSV",    command=self.export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit",             command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0, bg=PANEL_COLOR, fg=TEXT_COLOR)
        help_menu.add_command(label="About", command=self.show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    # ─────────────────────────────────────────
    # Header
    # ─────────────────────────────────────────

    def _build_header(self):
        """Build the top header banner."""
        header = tk.Frame(self.root, bg=HIGHLIGHT, height=55)
        header.pack(fill="x", side="top")

        tk.Label(
            header,
            text="🏈  NFL Schedule Builder",
            font=("Helvetica", 22, "bold"),
            bg=HIGHLIGHT,
            fg=TEXT_COLOR
        ).pack(side="left", padx=20, pady=10)

        self.file_label = tk.Label(
            header,
            text=f"File: {self.save_file}",
            font=("Helvetica", 10),
            bg=HIGHLIGHT,
            fg=TEXT_COLOR
        )
        self.file_label.pack(side="right", padx=20)

    # ─────────────────────────────────────────
    # Main Layout
    # ─────────────────────────────────────────

    def _build_main_layout(self):
        """Build the two-panel main layout."""
        main_frame = tk.Frame(self.root, bg=BG_COLOR)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel: form
        left = tk.Frame(main_frame, bg=PANEL_COLOR, width=320, relief="flat", bd=2)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)
        self._build_form(left)

        # Right panel: schedule view
        right = tk.Frame(main_frame, bg=PANEL_COLOR, relief="flat", bd=2)
        right.pack(side="left", fill="both", expand=True)
        self._build_schedule_view(right)

    # ─────────────────────────────────────────
    # Left Panel: Game Entry Form
    # ─────────────────────────────────────────

    def _build_form(self, parent):
        """Build the game entry form with searchable team dropdowns."""

        tk.Label(
            parent,
            text="Add / Edit Game",
            font=("Helvetica", 14, "bold"),
            bg=PANEL_COLOR,
            fg=HIGHLIGHT
        ).pack(pady=(15, 5))

        tk.Frame(parent, bg=HIGHLIGHT, height=2).pack(fill="x", padx=15, pady=(0, 10))

        form = tk.Frame(parent, bg=PANEL_COLOR)
        form.pack(fill="x", padx=15)

        def label(text):
            """Helper: styled label."""
            tk.Label(
                form,
                text=text,
                font=("Helvetica", 10, "bold"),
                bg=PANEL_COLOR,
                fg=TEXT_COLOR,
                anchor="w"
            ).pack(fill="x", pady=(8, 1))

        def entry(default=""):
            """Helper: styled text entry."""
            e = tk.Entry(
                form,
                font=("Helvetica", 11),
                bg=ENTRY_BG,
                fg=TEXT_COLOR,
                insertbackground=TEXT_COLOR,
                relief="flat",
                bd=5
            )
            e.pack(fill="x", ipady=4)
            if default:
                e.insert(0, default)
            return e

        # ── Form Fields ──

        label("Week #")
        self.week_entry = entry()

        label("Date (MM/DD/YYYY or TBD)")
        self.date_entry = entry("TBD")

        # Away team: searchable combobox
        label("Away Team")
        self.away_combo = SearchableCombobox(form, values=NFL_TEAMS)
        self.away_combo.pack(fill="x")

        # Home team: searchable combobox
        label("Home Team")
        self.home_combo = SearchableCombobox(form, values=NFL_TEAMS)
        self.home_combo.pack(fill="x")

        label("Game Time (e.g. 1:00 PM ET)")
        self.time_entry = entry("TBD")

        label("Location / Stadium")
        self.location_entry = entry("TBD")

        label("Season Year")
        self.year_entry = entry(str(datetime.now().year))

        # ── Buttons ──
        tk.Frame(parent, bg=HIGHLIGHT, height=2).pack(fill="x", padx=15, pady=15)

        btn_frame = tk.Frame(parent, bg=PANEL_COLOR)
        btn_frame.pack(fill="x", padx=15)

        def styled_btn(text, cmd, color=BUTTON_COLOR):
            return tk.Button(
                btn_frame,
                text=text,
                command=cmd,
                font=("Helvetica", 11, "bold"),
                bg=color,
                fg=BUTTON_TEXT,
                relief="flat",
                bd=0,
                padx=10,
                pady=8,
                cursor="hand2",
                activebackground=HIGHLIGHT,
                activeforeground=TEXT_COLOR
            )

        styled_btn("➕  Add Game",    self.add_game,    HIGHLIGHT).pack(fill="x", pady=3)
        styled_btn("✏️  Update Game", self.update_game, BUTTON_COLOR).pack(fill="x", pady=3)
        styled_btn("🔄  Clear Form",  self.clear_form,  ACCENT_COLOR).pack(fill="x", pady=3)
        styled_btn("🗑️  Delete Game", self.delete_game, "#8b0000").pack(fill="x", pady=3)

    # ─────────────────────────────────────────
    # Right Panel: Schedule Treeview
    # ─────────────────────────────────────────

    def _build_schedule_view(self, parent):
        """Build the schedule treeview."""

        top_bar = tk.Frame(parent, bg=PANEL_COLOR)
        top_bar.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(
            top_bar,
            text="Schedule View",
            font=("Helvetica", 14, "bold"),
            bg=PANEL_COLOR,
            fg=HIGHLIGHT
        ).pack(side="left")

        tk.Label(
            top_bar,
            text="Filter by Team:",
            font=("Helvetica", 10),
            bg=PANEL_COLOR,
            fg=TEXT_COLOR
        ).pack(side="left", padx=(20, 5))

        # Team filter: also a searchable combobox
        self.filter_combo = SearchableCombobox(
            top_bar,
            values=["All Teams"] + NFL_TEAMS,
            placeholder="All Teams",
            font=("Helvetica", 10)
        )
        self.filter_combo.pack(side="left")
        # Bind Enter key on filter to refresh
        self.filter_combo.entry.bind("<Return>", lambda e: self.refresh_schedule_view())
        self.filter_combo.entry.bind("<FocusOut>", lambda e: self.after(200, self.refresh_schedule_view))

        # Apply filter button
        tk.Button(
            top_bar,
            text="Apply",
            command=self.refresh_schedule_view,
            font=("Helvetica", 9, "bold"),
            bg=HIGHLIGHT,
            fg=TEXT_COLOR,
            relief="flat",
            padx=8,
            pady=3,
            cursor="hand2"
        ).pack(side="left", padx=(5, 0))

        # Clear filter button
        tk.Button(
            top_bar,
            text="Clear",
            command=self._clear_filter,
            font=("Helvetica", 9),
            bg=ACCENT_COLOR,
            fg=TEXT_COLOR,
            relief="flat",
            padx=8,
            pady=3,
            cursor="hand2"
        ).pack(side="left", padx=(3, 0))

        # Search bar
        tk.Label(
            top_bar,
            text="Search:",
            font=("Helvetica", 10),
            bg=PANEL_COLOR,
            fg=TEXT_COLOR
        ).pack(side="left", padx=(15, 5))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self.refresh_schedule_view())
        tk.Entry(
            top_bar,
            textvariable=self.search_var,
            font=("Helvetica", 10),
            bg=ENTRY_BG,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat",
            bd=4,
            width=18
        ).pack(side="left")

        # Treeview styling
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "NFL.Treeview",
            background=TREE_BG,
            foreground=TREE_FG,
            fieldbackground=TREE_BG,
            rowheight=28,
            font=("Helvetica", 10)
        )
        style.configure(
            "NFL.Treeview.Heading",
            background=ACCENT_COLOR,
            foreground=TEXT_COLOR,
            font=("Helvetica", 10, "bold"),
            relief="flat"
        )
        style.map(
            "NFL.Treeview",
            background=[("selected", TREE_SELECT)],
            foreground=[("selected", TEXT_COLOR)]
        )

        columns = ("week", "date", "away", "home", "time", "location", "year")
        tree_frame = tk.Frame(parent, bg=PANEL_COLOR)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            style="NFL.Treeview",
            selectmode="browse"
        )

        col_config = {
            "week":     ("Week",      55),
            "date":     ("Date",     170),
            "away":     ("Away Team",175),
            "home":     ("Home Team",175),
            "time":     ("Time",     110),
            "location": ("Location", 170),
            "year":     ("Season",    65)
        }
        for col, (heading, width) in col_config.items():
            self.tree.heading(col, text=heading, command=lambda c=col: self.sort_tree(c))
            self.tree.column(col, width=width, anchor="center")

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
            parent,
            text="",
            font=("Helvetica", 9, "italic"),
            bg=PANEL_COLOR,
            fg=TEXT_COLOR
        )
        self.count_label.pack(anchor="e", padx=15, pady=(0, 5))

    # ─────────────────────────────────────────
    # Status Bar
    # ─────────────────────────────────────────

    def _build_status_bar(self):
        """Build the bottom status bar."""
        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Helvetica", 9),
            bg=ACCENT_COLOR,
            fg=TEXT_COLOR,
            anchor="w",
            padx=10
        ).pack(fill="x", side="bottom")

    # ─────────────────────────────────────────
    # Core Game Functions
    # ─────────────────────────────────────────

    def add_game(self):
        """Validate and add a new game."""
        game = self._get_form_data()
        if game is None:
            return

        for g in self.games:
            if (g["week"] == game["week"] and
                g["home_team"] == game["home_team"] and
                g["away_team"] == game["away_team"] and
                g["year"] == game["year"]):
                messagebox.showwarning("Duplicate Game", "This game already exists.")
                return

        self.games.append(game)
        self._save_and_refresh(f"Added: Week {game['week']} | {game['away_team']} @ {game['home_team']}")
        self.clear_form()

    def update_game(self):
        """Update the selected game with current form data."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Click a game in the schedule to select it first.")
            return
        game = self._get_form_data()
        if game is None:
            return
        idx = int(self.tree.item(selected[0], "tags")[0])
        self.games[idx] = game
        self._save_and_refresh(f"Updated: Week {game['week']} | {game['away_team']} @ {game['home_team']}")

    def delete_game(self):
        """Delete the selected game after confirmation."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Click a game to select it first.")
            return
        idx = int(self.tree.item(selected[0], "tags")[0])
        g = self.games[idx]
        if messagebox.askyesno("Confirm Delete",
                               f"Delete Week {g['week']} | {g['away_team']} @ {g['home_team']}?"):
            self.games.pop(idx)
            self._save_and_refresh(f"Deleted: Week {g['week']} | {g['away_team']} @ {g['home_team']}")
            self.clear_form()

    def _get_form_data(self):
        """Read, validate, and return form data as a dict, or None on failure."""

        # Week validation
        week_str = self.week_entry.get().strip()
        if not week_str.isdigit() or not (1 <= int(week_str) <= 23):
            messagebox.showerror("Invalid Week", "Week must be a number between 1 and 23.")
            return None

        # Team validation
        away = self.away_combo.get()
        home = self.home_combo.get()
        if not away or not home:
            messagebox.showerror("Missing Teams", "Please select both home and away teams.")
            return None
        if away not in NFL_TEAMS or home not in NFL_TEAMS:
            messagebox.showerror("Invalid Team", "Please select a valid NFL team from the list.")
            return None
        if away == home:
            messagebox.showerror("Same Team", "Home and Away teams cannot be the same.")
            return None

        # Date validation
        date_str = self.date_entry.get().strip()
        if date_str.upper() != "TBD":
            try:
                date_str = datetime.strptime(date_str, "%m/%d/%Y").strftime("%m/%d/%Y")
            except ValueError:
                messagebox.showerror("Invalid Date", "Date must be MM/DD/YYYY or 'TBD'.")
                return None

        # Year validation
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
        """Reset all form fields to defaults."""
        self.week_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END);     self.date_entry.insert(0, "TBD")
        self.away_combo.clear()
        self.home_combo.clear()
        self.time_entry.delete(0, tk.END);     self.time_entry.insert(0, "TBD")
        self.location_entry.delete(0, tk.END); self.location_entry.insert(0, "TBD")
        self.year_entry.delete(0, tk.END);     self.year_entry.insert(0, str(datetime.now().year))
        self.tree.selection_remove(self.tree.selection())

    def on_row_select(self, event):
        """Populate form when a schedule row is clicked."""
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
        """Refresh treeview applying team filter and search."""
        for row in self.tree.get_children():
            self.tree.delete(row)

        # Get filter value (ignore placeholder text)
        team_filter = self.filter_combo.get()
        if not team_filter or team_filter == "All Teams":
            team_filter = None

        search_term = self.search_var.get().strip().lower()

        sorted_games = sorted(self.games, key=lambda g: (g.get("year", 0), g["week"]))

        visible = 0
        for idx, g in enumerate(self.games):
            # Team filter
            if team_filter:
                if g["home_team"] != team_filter and g["away_team"] != team_filter:
                    continue
            # Search filter
            if search_term:
                if search_term not in " ".join(str(v).lower() for v in g.values()):
                    continue

            tag = "even" if visible % 2 == 0 else "odd"
            self.tree.insert(
                "", "end",
                values=(
                    g["week"], g["date"], g["away_team"],
                    g["home_team"], g["time"], g["location"], g.get("year", "N/A")
                ),
                tags=(str(idx), tag)
            )
            visible += 1

        self.tree.tag_configure("even", background=TREE_BG)
        self.tree.tag_configure("odd",  background="#111122")
        self.count_label.config(text=f"Showing {visible} of {len(self.games)} game(s)")

    def _clear_filter(self):
        """Reset the team filter and refresh."""
        self.filter_combo.clear()
        self.refresh_schedule_view()

    def refresh_team_filter(self):
        """Rebuild the team filter dropdown options."""
        teams = set()
        for g in self.games:
            teams.add(g["home_team"])
            teams.add(g["away_team"])
        self.filter_combo.all_values = ["All Teams"] + sorted(teams)

    def sort_tree(self, col):
        """Sort treeview rows by clicked column header."""
        col_map = {
            "week": "week", "date": "date", "away": "away_team",
            "home": "home_team", "time": "time",
            "location": "location", "year": "year"
        }
        key = col_map.get(col, col)
        self.games.sort(key=lambda g: str(g.get(key, "")))
        self.refresh_schedule_view()
        self.update_status(f"Sorted by: {col}")

    # ─────────────────────────────────────────
    # File Operations
    # ─────────────────────────────────────────

    def _save_and_refresh(self, msg=""):
        """Save to file and refresh the view."""
        save_games(self.save_file, self.games)
        self.refresh_schedule_view()
        self.refresh_team_filter()
        self.update_status(msg + f" | Saved to '{self.save_file}'")

    def save_now(self):
        """Manual save."""
        save_games(self.save_file, self.games)
        self.update_status(f"Saved {len(self.games)} game(s) to '{self.save_file}'")

    def save_as(self):
        """Save to a new file path."""
        path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Save Schedule As"
        )
        if path:
            self.save_file = path
            self.file_label.config(text=f"File: {self.save_file}")
            save_games(self.save_file, self.games)
            self.update_status(f"Saved to '{self.save_file}'")

    def open_schedule(self):
        """Open a different JSON schedule file."""
        path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Open Schedule File"
        )
        if path:
            self.save_file = path
            self.games = load_games(self.save_file)
            self.file_label.config(text=f"File: {self.save_file}")
            self.refresh_schedule_view()
            self.refresh_team_filter()
            self.update_status(f"Opened '{self.save_file}' | {len(self.games)} game(s) loaded")

    def new_schedule(self):
        """Start a fresh schedule."""
        if messagebox.askyesno("New Schedule", "Start a new schedule? Unsaved changes will be lost."):
            self.games = []
            self.save_file = DEFAULT_SAVE_FILE
            self.file_label.config(text=f"File: {self.save_file}")
            self.refresh_schedule_view()
            self.refresh_team_filter()
            self.clear_form()
            self.update_status("New schedule started.")

    def export_csv(self):
        """Export schedule to CSV."""
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
                    f, fieldnames=["year","week","date","away_team","home_team","time","location"]
                )
                writer.writeheader()
                for g in sorted(self.games, key=lambda x: (x.get("year", 0), x["week"])):
                    writer.writerow(g)
            self.update_status(f"Exported {len(self.games)} game(s) to '{path}'")

    # ─────────────────────────────────────────
    # Utility
    # ─────────────────────────────────────────

    def update_status(self, msg):
        """Update bottom status bar text."""
        self.status_var.set(f"  {msg}")

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About NFL Schedule Builder",
            "🏈 NFL Schedule Builder\n\n"
            "Build your NFL season schedule with ease.\n\n"
            "Searchable team dropdowns — just start typing!\n\n"
            "Features:\n"
            "  • Searchable team dropdowns\n"
            "  • Add, edit, delete games\n"
            "  • Filter & search schedule\n"
            "  • Sort by any column\n"
            "  • Auto-save to JSON\n"
            "  • Export to CSV"
        )


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = NFLSchedulerApp(root)
    root.mainloop()