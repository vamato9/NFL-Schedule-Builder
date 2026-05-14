# NFL Schedule Builder - GUI Version
# Uses Tkinter for the interface and JSON for persistent file storage

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime
from collections import defaultdict

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
BG_COLOR       = "#1a1a2e"   # Dark navy background
PANEL_COLOR    = "#16213e"   # Slightly lighter panel
ACCENT_COLOR   = "#0f3460"   # Deep blue accent
HIGHLIGHT      = "#e94560"   # Red highlight (NFL feel)
TEXT_COLOR     = "#eaeaea"   # Light text
BUTTON_COLOR   = "#0f3460"   # Button background
BUTTON_TEXT    = "#ffffff"   # Button text
ENTRY_BG       = "#0d0d1a"   # Entry background
TREE_BG        = "#0d0d1a"   # Treeview background
TREE_FG        = "#eaeaea"   # Treeview foreground
TREE_SELECT    = "#e94560"   # Treeview selected row

# ─────────────────────────────────────────────
# File I/O Functions
# ─────────────────────────────────────────────

def load_games(filepath):
    """
    Load games from a JSON file.
    Returns a list of game dictionaries.
    """
    if os.path.exists(filepath):
        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                return data.get("games", [])
        except (json.JSONDecodeError, KeyError):
            # If file is corrupted, start fresh
            messagebox.showwarning("Load Warning", f"Could not read '{filepath}'. Starting fresh.")
            return []
    return []


def save_games(filepath, games):
    """
    Save games list to a JSON file.
    Wraps data in a dict with metadata.
    """
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
        """
        Initialize the main application window.
        """
        self.root = root
        self.root.title("🏈 NFL Schedule Builder")
        self.root.geometry("1200x750")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(True, True)

        # Current save file path
        self.save_file = DEFAULT_SAVE_FILE

        # Load existing games from file
        self.games = load_games(self.save_file)

        # Build the UI
        self._build_menu()
        self._build_header()
        self._build_main_layout()
        self._build_status_bar()

        # Populate the schedule view on load
        self.refresh_schedule_view()
        self.refresh_team_filter()
        self.update_status(f"Loaded {len(self.games)} game(s) from '{self.save_file}'")

    # ─────────────────────────────────────────
    # Menu Bar
    # ─────────────────────────────────────────

    def _build_menu(self):
        """Build the top menu bar."""
        menubar = tk.Menu(self.root, bg=ACCENT_COLOR, fg=TEXT_COLOR, tearoff=0)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg=PANEL_COLOR, fg=TEXT_COLOR)
        file_menu.add_command(label="New Schedule",    command=self.new_schedule)
        file_menu.add_command(label="Open Schedule...", command=self.open_schedule)
        file_menu.add_command(label="Save",            command=self.save_now)
        file_menu.add_command(label="Save As...",      command=self.save_as)
        file_menu.add_separator()
        file_menu.add_command(label="Export to CSV",   command=self.export_csv)
        file_menu.add_separator()
        file_menu.add_command(label="Exit",            command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Help menu
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

        # Save file label shown in header
        self.file_label = tk.Label(
            header,
            text=f"File: {self.save_file}",
            font=("Helvetica", 10),
            bg=HIGHLIGHT,
            fg=TEXT_COLOR
        )
        self.file_label.pack(side="right", padx=20)

    # ─────────────────────────────────────────
    # Main Layout (Left Panel + Right Panel)
    # ─────────────────────────────────────────

    def _build_main_layout(self):
        """Build the two-panel main layout."""
        main_frame = tk.Frame(self.root, bg=BG_COLOR)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Left panel: Add/Edit game form
        left = tk.Frame(main_frame, bg=PANEL_COLOR, width=320, relief="flat", bd=2)
        left.pack(side="left", fill="y", padx=(0, 10))
        left.pack_propagate(False)
        self._build_form(left)

        # Right panel: Schedule view
        right = tk.Frame(main_frame, bg=PANEL_COLOR, relief="flat", bd=2)
        right.pack(side="left", fill="both", expand=True)
        self._build_schedule_view(right)

    # ─────────────────────────────────────────
    # Left Panel: Game Entry Form
    # ─────────────────────────────────────────

    def _build_form(self, parent):
        """Build the game entry form on the left panel."""

        # Section title
        tk.Label(
            parent,
            text="Add / Edit Game",
            font=("Helvetica", 14, "bold"),
            bg=PANEL_COLOR,
            fg=HIGHLIGHT
        ).pack(pady=(15, 5))

        tk.Frame(parent, bg=HIGHLIGHT, height=2).pack(fill="x", padx=15, pady=(0, 10))

        # Form container
        form = tk.Frame(parent, bg=PANEL_COLOR)
        form.pack(fill="x", padx=15)

        def label(text):
            """Helper to create a styled label."""
            tk.Label(
                form,
                text=text,
                font=("Helvetica", 10, "bold"),
                bg=PANEL_COLOR,
                fg=TEXT_COLOR,
                anchor="w"
            ).pack(fill="x", pady=(8, 1))

        def entry():
            """Helper to create a styled entry field."""
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
            return e

        def combobox(values):
            """Helper to create a styled combobox."""
            cb = ttk.Combobox(
                form,
                values=values,
                font=("Helvetica", 11),
                state="readonly"
            )
            cb.pack(fill="x", ipady=4)
            return cb

        # ── Form Fields ──
        label("Week #")
        self.week_entry = entry()

        label("Date (MM/DD/YYYY or TBD)")
        self.date_entry = entry()
        self.date_entry.insert(0, "TBD")

        label("Away Team")
        self.away_combo = combobox(NFL_TEAMS)

        label("Home Team")
        self.home_combo = combobox(NFL_TEAMS)

        label("Game Time (e.g. 1:00 PM ET)")
        self.time_entry = entry()
        self.time_entry.insert(0, "TBD")

        label("Location / Stadium")
        self.location_entry = entry()
        self.location_entry.insert(0, "TBD")

        label("Season Year")
        self.year_entry = entry()
        self.year_entry.insert(0, str(datetime.now().year))

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

        # Add Game button
        styled_btn("➕  Add Game",    self.add_game,    HIGHLIGHT).pack(fill="x", pady=3)
        # Update selected game button
        styled_btn("✏️  Update Game", self.update_game, BUTTON_COLOR).pack(fill="x", pady=3)
        # Clear form button
        styled_btn("🔄  Clear Form",  self.clear_form,  ACCENT_COLOR).pack(fill="x", pady=3)
        # Delete selected game button
        styled_btn("🗑️  Delete Game", self.delete_game, "#8b0000").pack(fill="x", pady=3)

    # ─────────────────────────────────────────
    # Right Panel: Schedule Treeview
    # ─────────────────────────────────────────

    def _build_schedule_view(self, parent):
        """Build the schedule display treeview on the right panel."""

        # Top bar: title + filter
        top_bar = tk.Frame(parent, bg=PANEL_COLOR)
        top_bar.pack(fill="x", padx=10, pady=(10, 5))

        tk.Label(
            top_bar,
            text="Schedule View",
            font=("Helvetica", 14, "bold"),
            bg=PANEL_COLOR,
            fg=HIGHLIGHT
        ).pack(side="left")

        # Team filter dropdown
        tk.Label(
            top_bar,
            text="Filter by Team:",
            font=("Helvetica", 10),
            bg=PANEL_COLOR,
            fg=TEXT_COLOR
        ).pack(side="left", padx=(20, 5))

        self.filter_var = tk.StringVar(value="All Teams")
        self.team_filter = ttk.Combobox(
            top_bar,
            textvariable=self.filter_var,
            font=("Helvetica", 10),
            state="readonly",
            width=25
        )
        self.team_filter.pack(side="left")
        self.team_filter.bind("<<ComboboxSelected>>", lambda e: self.refresh_schedule_view())

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
            width=20
        ).pack(side="left")

        # Treeview style
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

        # Treeview columns
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

        # Define column headers and widths
        col_config = {
            "week":     ("Week",     55),
            "date":     ("Date",     170),
            "away":     ("Away Team", 175),
            "home":     ("Home Team", 175),
            "time":     ("Time",     110),
            "location": ("Location", 170),
            "year":     ("Season",    65)
        }
        for col, (heading, width) in col_config.items():
            self.tree.heading(col, text=heading, command=lambda c=col: self.sort_tree(c))
            self.tree.column(col, width=width, anchor="center")

        # Scrollbars
        vsb = ttk.Scrollbar(tree_frame, orient="vertical",   command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        tree_frame.rowconfigure(0, weight=1)
        tree_frame.columnconfigure(0, weight=1)

        # Bind row click to populate form for editing
        self.tree.bind("<<TreeviewSelect>>", self.on_row_select)

        # Row count label
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
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            font=("Helvetica", 9),
            bg=ACCENT_COLOR,
            fg=TEXT_COLOR,
            anchor="w",
            padx=10
        )
        status_bar.pack(fill="x", side="bottom")

    # ─────────────────────────────────────────
    # Core Game Functions
    # ─────────────────────────────────────────

    def add_game(self):
        """Validate form and add a new game to the list, then save."""
        game = self._get_form_data()
        if game is None:
            return  # Validation failed

        # Check for duplicate
        for g in self.games:
            if (g["week"] == game["week"] and
                g["home_team"] == game["home_team"] and
                g["away_team"] == game["away_team"] and
                g["year"] == game["year"]):
                messagebox.showwarning("Duplicate Game", "This game already exists in the schedule.")
                return

        self.games.append(game)
        self._save_and_refresh(f"Game added: Week {game['week']} | {game['away_team']} @ {game['home_team']}")
        self.clear_form()

    def update_game(self):
        """Update the currently selected game with form data."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please click a game in the schedule to select it first.")
            return

        game = self._get_form_data()
        if game is None:
            return

        # Get the index stored in the tree item
        idx = self.tree.item(selected[0], "tags")[0]
        idx = int(idx)
        self.games[idx] = game
        self._save_and_refresh(f"Game updated: Week {game['week']} | {game['away_team']} @ {game['home_team']}")

    def delete_game(self):
        """Delete the currently selected game."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please click a game to select it first.")
            return

        idx = int(self.tree.item(selected[0], "tags")[0])
        g = self.games[idx]
        confirm = messagebox.askyesno(
            "Confirm Delete",
            f"Delete: Week {g['week']} | {g['away_team']} @ {g['home_team']}?"
        )
        if confirm:
            self.games.pop(idx)
            self._save_and_refresh(f"Game deleted: Week {g['week']} | {g['away_team']} @ {g['home_team']}")
            self.clear_form()

    def _get_form_data(self):
        """
        Read and validate all form fields.
        Returns a game dict or None if validation fails.
        """
        # Validate week
        week_str = self.week_entry.get().strip()
        if not week_str.isdigit() or not (1 <= int(week_str) <= 23):
            messagebox.showerror("Invalid Week", "Week must be a number between 1 and 23.")
            return None

        # Validate teams
        away = self.away_combo.get().strip()
        home = self.home_combo.get().strip()
        if not away or not home:
            messagebox.showerror("Missing Teams", "Please select both home and away teams.")
            return None
        if away == home:
            messagebox.showerror("Same Team", "Home and Away teams cannot be the same.")
            return None

        # Validate date
        date_str = self.date_entry.get().strip()
        if date_str.upper() != "TBD":
            try:
                date_str = datetime.strptime(date_str, "%m/%d/%Y").strftime("%m/%d/%Y")
            except ValueError:
                messagebox.showerror("Invalid Date", "Date must be in MM/DD/YYYY format or 'TBD'.")
                return None

        # Validate year
        year_str = self.year_entry.get().strip()
        if not year_str.isdigit():
            messagebox.showerror("Invalid Year", "Please enter a valid 4-digit year.")
            return None

        return {
            "week":      int(week_str),
            "date":      date_str.upper() if date_str.upper() == "TBD" else date_str,
            "away_team": away,
            "home_team": home,
            "time":      self.time_entry.get().strip() or "TBD",
            "location":  self.location_entry.get().strip() or "TBD",
            "year":      int(year_str)
        }

    def clear_form(self):
        """Clear all form fields back to defaults."""
        self.week_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END);     self.date_entry.insert(0, "TBD")
        self.away_combo.set("")
        self.home_combo.set("")
        self.time_entry.delete(0, tk.END);     self.time_entry.insert(0, "TBD")
        self.location_entry.delete(0, tk.END); self.location_entry.insert(0, "TBD")
        self.year_entry.delete(0, tk.END);     self.year_entry.insert(0, str(datetime.now().year))
        self.tree.selection_remove(self.tree.selection())

    def on_row_select(self, event):
        """When a row is clicked, populate the form with that game's data."""
        selected = self.tree.selection()
        if not selected:
            return
        idx = int(self.tree.item(selected[0], "tags")[0])
        g = self.games[idx]

        # Populate form fields
        self.week_entry.delete(0, tk.END);     self.week_entry.insert(0, str(g["week"]))
        self.date_entry.delete(0, tk.END);     self.date_entry.insert(0, g["date"])
        self.away_combo.set(g["away_team"])
        self.home_combo.set(g["home_team"])
        self.time_entry.delete(0, tk.END);     self.time_entry.insert(0, g["time"])
        self.location_entry.delete(0, tk.END); self.location_entry.insert(0, g["location"])
        self.year_entry.delete(0, tk.END);     self.year_entry.insert(0, str(g["year"]))

    # ─────────────────────────────────────────
    # Schedule View Refresh
    # ─────────────────────────────────────────

    def refresh_schedule_view(self):
        """Refresh the treeview with current games, applying filter and search."""
        # Clear existing rows
        for row in self.tree.get_children():
            self.tree.delete(row)

        team_filter = self.filter_var.get()
        search_term = self.search_var.get().strip().lower()

        # Sort games by year, then week
        sorted_games = sorted(self.games, key=lambda g: (g.get("year", 0), g["week"]))

        visible = 0
        for idx, g in enumerate(self.games):
            # Apply team filter
            if team_filter != "All Teams":
                if g["home_team"] != team_filter and g["away_team"] != team_filter:
                    continue

            # Apply search filter
            if search_term:
                searchable = " ".join(str(v).lower() for v in g.values())
                if search_term not in searchable:
                    continue

            # Alternate row colors for readability
            tag = "even" if visible % 2 == 0 else "odd"
            self.tree.insert(
                "", "end",
                values=(
                    g["week"],
                    g["date"],
                    g["away_team"],
                    g["home_team"],
                    g["time"],
                    g["location"],
                    g.get("year", "N/A")
                ),
                tags=(str(idx), tag)  # Store original index as tag
            )
            visible += 1

        # Alternate row colors
        self.tree.tag_configure("even", background=TREE_BG)
        self.tree.tag_configure("odd",  background="#111122")

        self.count_label.config(text=f"Showing {visible} of {len(self.games)} game(s)")

    def refresh_team_filter(self):
        """Update the team filter dropdown with all teams currently in schedule."""
        teams = set()
        for g in self.games:
            teams.add(g["home_team"])
            teams.add(g["away_team"])
        options = ["All Teams"] + sorted(teams)
        self.team_filter["values"] = options
        self.filter_var.set("All Teams")

    def sort_tree(self, col):
        """Sort the treeview by a column when the header is clicked."""
        col_map = {
            "week": "week", "date": "date", "away": "away_team",
            "home": "home_team", "time": "time",
            "location": "location", "year": "year"
        }
        key = col_map.get(col, col)
        self.games.sort(key=lambda g: (str(g.get(key, ""))))
        self.refresh_schedule_view()
        self.update_status(f"Sorted by: {col}")

    # ─────────────────────────────────────────
    # Save / Load / Export
    # ─────────────────────────────────────────

    def _save_and_refresh(self, status_msg=""):
        """Save games to file and refresh the view."""
        save_games(self.save_file, self.games)
        self.refresh_schedule_view()
        self.refresh_team_filter()
        self.update_status(status_msg + f" | Auto-saved to '{self.save_file}'")

    def save_now(self):
        """Manually save to current file."""
        save_games(self.save_file, self.games)
        self.update_status(f"Saved {len(self.games)} game(s) to '{self.save_file}'")

    def save_as(self):
        """Save to a new file chosen by user."""
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
        """Open a different schedule JSON file."""
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
        """Start a fresh empty schedule."""
        confirm = messagebox.askyesno("New Schedule", "Start a new schedule? Unsaved changes will be lost.")
        if confirm:
            self.games = []
            self.save_file = DEFAULT_SAVE_FILE
            self.file_label.config(text=f"File: {self.save_file}")
            self.refresh_schedule_view()
            self.refresh_team_filter()
            self.clear_form()
            self.update_status("New schedule started.")

    def export_csv(self):
        """Export the current schedule to a CSV file."""
        if not self.games:
            messagebox.showinfo("Empty", "No games to export.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")],
            title="Export Schedule to CSV"
        )
        if path:
            import csv
            with open(path, "w", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=["year","week","date","away_team","home_team","time","location"])
                writer.writeheader()
                for g in sorted(self.games, key=lambda x: (x.get("year", 0), x["week"])):
                    writer.writerow(g)
            self.update_status(f"Exported {len(self.games)} game(s) to '{path}'")

    # ─────────────────────────────────────────
    # Utility
    # ─────────────────────────────────────────

    def update_status(self, msg):
        """Update the bottom status bar."""
        self.status_var.set(f"  {msg}")

    def show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "About NFL Schedule Builder",
            "🏈 NFL Schedule Builder\n\n"
            "Enter known game matchups and dates\n"
            "to build a full NFL season schedule.\n\n"
            "Data is saved automatically to a JSON file\n"
            "which can be backed up at any time.\n\n"
            "Features:\n"
            "  • Add, edit, delete games\n"
            "  • Filter by team\n"
            "  • Search across all fields\n"
            "  • Sort by any column\n"
            "  • Export to CSV\n"
            "  • Auto-save on every change"
        )


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    root = tk.Tk()
    app = NFLSchedulerApp(root)
    root.mainloop()