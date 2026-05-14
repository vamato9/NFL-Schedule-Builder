# NFL Schedule Builder - GUI Version with Searchable Dropdowns + Week Filter
# Fixed: week number now sorts numerically (int) not alphabetically (string)

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import json
import os
from datetime import datetime

# ─────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────

DEFAULT_SAVE_FILE = "nfl_schedule.json"

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
BG_COLOR     = "#1a1a2e"
PANEL_COLOR  = "#16213e"
ACCENT_COLOR = "#0f3460"
HIGHLIGHT    = "#e94560"
TEXT_COLOR   = "#eaeaea"
BUTTON_COLOR = "#0f3460"
BUTTON_TEXT  = "#ffffff"
ENTRY_BG     = "#0d0d1a"
TREE_BG      = "#0d0d1a"
TREE_FG      = "#eaeaea"
TREE_SELECT  = "#e94560"

# ─────────────────────────────────────────────
# Searchable Combobox Widget
# ─────────────────────────────────────────────

class SearchableCombobox(tk.Frame):
    """
    A custom searchable combobox widget.
    Filters the dropdown list in real time as the user types.
    Closes the dropdown when clicking anywhere outside of it.
    """

    # Class-level registry so we can close all others when one opens
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

        # Register this instance
        SearchableCombobox._all_instances.append(self)

        # ── Entry Field ──
        self.var = tk.StringVar()
        self.var.trace("w", self._on_type)

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

        self._show_placeholder()

        # ── Bind Entry Events ──
        self.entry.bind("<FocusIn>",  self._on_focus_in)
        self.entry.bind("<FocusOut>", self._on_focus_out)
        self.entry.bind("<Down>",     self._focus_listbox)
        self.entry.bind("<Return>",   self._on_entry_return)
        self.entry.bind("<Escape>",   lambda e: self._close_dropdown())

        # Bind global click after widget is ready
        self.after(100, self._bind_global_click)

    def _bind_global_click(self):
        """Bind a global click listener to detect outside clicks."""
        self.entry.bind_all("<ButtonPress-1>", self._on_global_click, add="+")

    def _get_root(self):
        """Walk up the widget tree to find the root Tk window."""
        widget = self
        while widget.master:
            widget = widget.master
        return widget

    def _on_global_click(self, event):
        """
        Close this dropdown if the click was outside
        the entry widget and the dropdown window.
        """
        if not self._dropdown_open:
            return

        clicked_widget = event.widget

        # Ignore clicks on our own entry
        if clicked_widget == self.entry:
            return

        # Ignore clicks on our own listbox
        if self._listbox and clicked_widget == self._listbox:
            return

        # Check if click landed inside the dropdown bounding box
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

        # Click was outside — close dropdown
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
        """Remove placeholder when user focuses the field."""
        if getattr(self, "_has_placeholder", False):
            self.var.set("")
            self.entry.config(fg=TEXT_COLOR)
            self._has_placeholder = False

    def _on_focus_in(self, event):
        """Clear placeholder and open dropdown on focus."""
        self._clear_placeholder()
        self._close_all_others()
        self._open_dropdown(self.all_values)

    def _on_focus_out(self, event):
        """Fallback close for keyboard-based focus changes."""
        if self._ignore_focus_out:
            return
        self.after(200, self._check_close_on_focus_out)

    def _check_close_on_focus_out(self):
        """Close dropdown if focus moved away via keyboard."""
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
        """Filter the dropdown list as the user types."""
        if getattr(self, "_has_placeholder", False):
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
        """Handle Enter key on a listbox item."""
        self._select_current()

    def _select_current(self):
        """Set the entry to the selected listbox item."""
        if self._listbox:
            sel = self._listbox.curselection()
            if sel:
                value = self._listbox.get(sel[0])
                self._has_placeholder = False
                self.var.set(value)
                self.entry.config(fg=TEXT_COLOR)
        self._close_dropdown()
        self._ignore_focus_out = False
        self.entry.focus_set()

    def _on_entry_return(self, event):
        """Auto-select if only one match remains on Enter."""
        typed = self.var.get().strip().lower()
        matches = [t for t in self.all_values if typed in t.lower()]
        if len(matches) == 1:
            self.var.set(matches[0])
            self.entry.config(fg=TEXT_COLOR)
            self._has_placeholder = False
            self._close_dropdown()

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
        self._has_placeholder = False
        self.var.set(value)
        self.entry.config(fg=TEXT_COLOR)
        self._close_dropdown()

    def clear(self):
        """Clear entry and restore placeholder."""
        self._close_dropdown()
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
            messagebox.showwarning("Load Warning", f"Could not read '{filepath}'. Starting fresh.")
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
    """
    Return a sort key for a game dict by column.
    Week and year are cast to int so they sort numerically.
    All other columns sort as lowercase strings.
    """
    val = game.get(col_key, "")

    # ── Numeric columns: sort as int ──
    if col_key in ("week", "year"):
        try:
            return (0, int(val))         # (0, int) sorts before (1, str) fallback
        except (ValueError, TypeError):
            return (1, str(val).lower()) # Fallback for non-numeric values

    # ── All other columns: sort as lowercase string ──
    return (0, str(val).lower())


# ─────────────────────────────────────────────
# Main Application
# ─────────────────────────────────────────────

class NFLSchedulerApp:
    def __init__(self, root):
        """Initialize the main application."""
        self.root = root
        self.root.title("🏈 NFL Schedule Builder")
        self.root.geometry("1280x780")
        self.root.configure(bg=BG_COLOR)
        self.root.resizable(True, True)

        # Track sort state per column: True = ascending, False = descending
        self._sort_ascending = {}

        self.save_file = DEFAULT_SAVE_FILE
        self.games     = load_games(self.save_file)

        self._build_menu()
        self._build_header()
        self._build_main_layout()
        self._build_status_bar()

        self.refresh_schedule_view()
        self.refresh_filter_options()
        self.update_status(f"Loaded {len(self.games)} game(s) from '{self.save_file}'")

    # ─────────────────────────────────────────
    # Menu Bar
    # ─────────────────────────────────────────

    def _build_menu(self):
        """Build the top menu bar."""
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
        """Build the game entry form."""

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
            tk.Label(
                form,
                text=text,
                font=("Helvetica", 10, "bold"),
                bg=PANEL_COLOR,
                fg=TEXT_COLOR,
                anchor="w"
            ).pack(fill="x", pady=(8, 1))

        def entry(default=""):
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
    # Right Panel: Schedule View
    # ─────────────────────────────────────────

    def _build_schedule_view(self, parent):
        """Build the schedule treeview with team and week filters."""

        # ── Filter Bar ──
        filter_frame = tk.Frame(parent, bg=PANEL_COLOR)
        filter_frame.pack(fill="x", padx=10, pady=(10, 2))

        tk.Label(
            filter_frame,
            text="Schedule View",
            font=("Helvetica", 14, "bold"),
            bg=PANEL_COLOR,
            fg=HIGHLIGHT
        ).grid(row=0, column=0, sticky="w", padx=(0, 15))

        tk.Label(
            filter_frame,
            text="Team:",
            font=("Helvetica", 10, "bold"),
            bg=PANEL_COLOR,
            fg=TEXT_COLOR
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
            filter_frame,
            text="Week:",
            font=("Helvetica", 10, "bold"),
            bg=PANEL_COLOR,
            fg=TEXT_COLOR
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
            filter_frame,
            text="Apply",
            command=self.refresh_schedule_view,
            font=("Helvetica", 9, "bold"),
            bg=HIGHLIGHT,
            fg=TEXT_COLOR,
            relief="flat",
            padx=8, pady=3,
            cursor="hand2"
        ).grid(row=0, column=5, padx=(6, 2))

        tk.Button(
            filter_frame,
            text="Clear",
            command=self._clear_filters,
            font=("Helvetica", 9),
            bg=ACCENT_COLOR,
            fg=TEXT_COLOR,
            relief="flat",
            padx=8, pady=3,
            cursor="hand2"
        ).grid(row=0, column=6, padx=(2, 10))

        # ── Search Bar ──
        search_frame = tk.Frame(parent, bg=PANEL_COLOR)
        search_frame.pack(fill="x", padx=10, pady=(2, 6))

        tk.Label(
            search_frame,
            text="🔍 Search:",
            font=("Helvetica", 10, "bold"),
            bg=PANEL_COLOR,
            fg=TEXT_COLOR
        ).pack(side="left", padx=(0, 6))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", lambda *a: self.refresh_schedule_view())

        tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=("Helvetica", 10),
            bg=ENTRY_BG,
            fg=TEXT_COLOR,
            insertbackground=TEXT_COLOR,
            relief="flat",
            bd=4,
            width=30
        ).pack(side="left")

        self.filter_status_label = tk.Label(
            search_frame,
            text="",
            font=("Helvetica", 9, "italic"),
            bg=PANEL_COLOR,
            fg=HIGHLIGHT
        )
        self.filter_status_label.pack(side="left", padx=(15, 0))

        # ── Treeview Styling ──
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

        # ── Treeview ──
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
            self.tree.heading(
                col, text=heading,
                command=lambda c=col: self.sort_tree(c)
            )
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
            if (g["week"]      == game["week"] and
                g["home_team"] == game["home_team"] and
                g["away_team"] == game["away_team"] and
                g["year"]      == game["year"]):
                messagebox.showwarning("Duplicate Game", "This game already exists.")
                return
        self.games.append(game)
        self._save_and_refresh(
            f"Added: Week {game['week']} | {game['away_team']} @ {game['home_team']}"
        )
        self.clear_form()

    def update_game(self):
        """Update the selected game."""
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
        """Delete the selected game after confirmation."""
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
            self._save_and_refresh(
                f"Deleted: Week {g['week']} | {g['away_team']} @ {g['home_team']}"
            )
            self.clear_form()

    def _get_form_data(self):
        """Read and validate form fields. Returns game dict or None."""
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
        """Reset all form fields."""
        self.week_entry.delete(0, tk.END)
        self.date_entry.delete(0, tk.END);     self.date_entry.insert(0, "TBD")
        self.away_combo.clear()
        self.home_combo.clear()
        self.time_entry.delete(0, tk.END);     self.time_entry.insert(0, "TBD")
        self.location_entry.delete(0, tk.END); self.location_entry.insert(0, "TBD")
        self.year_entry.delete(0, tk.END);     self.year_entry.insert(0, str(datetime.now().year))
        self.tree.selection_remove(self.tree.selection())

    def on_row_select(self, event):
        """Populate the form when a row is clicked."""
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
        """Refresh treeview applying all active filters, sorted by year then week."""
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
        if team_filter:
            active_filters.append(f"Team: {team_filter}")
        if week_filter:
            active_filters.append(f"Week: {week_filter}")
        if search_term:
            active_filters.append(f'Search: "{search_term}"')

        self.filter_status_label.config(
            text=("Filters: " + "  |  ".join(active_filters)) if active_filters else ""
        )

        # ── Sort games by year (int) then week (int) before displaying ──
        # This is the key fix: both year and week are cast to int
        indexed_games = list(enumerate(self.games))
        indexed_games.sort(
            key=lambda x: (
                int(x[1].get("year", 0)),   # Sort year as int
                int(x[1].get("week", 0))    # Sort week as int — fixes the bug
            )
        )

        visible = 0
        for idx, g in indexed_games:

            if team_filter:
                if g["home_team"] != team_filter and g["away_team"] != team_filter:
                    continue

            if week_filter:
                if str(g["week"]) != week_filter:
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
        """Clear all filters and refresh."""
        self.filter_team_combo.clear()
        self.filter_week_combo.clear()
        self.search_var.set("")
        self.refresh_schedule_view()
        self.update_status("Filters cleared.")

    def refresh_filter_options(self):
        """Update filter dropdowns with values in current schedule."""
        teams = set()
        for g in self.games:
            teams.add(g["home_team"])
            teams.add(g["away_team"])
        self.filter_team_combo.update_values(["All Teams"] + sorted(teams))

        # ── Sort weeks numerically ──
        weeks = sorted(set(g["week"] for g in self.games), key=lambda w: int(w))
        self.filter_week_combo.update_values(
            ["All Weeks"] + [str(w) for w in weeks]
        )

    def sort_tree(self, col):
        """
        Sort the treeview by the clicked column header.
        Toggles ascending/descending on repeated clicks.
        Week and year sort as integers; all other columns sort as strings.
        """
        # Map treeview column id to game dict key
        col_map = {
            "week":     "week",
            "date":     "date",
            "away":     "away_team",
            "home":     "home_team",
            "time":     "time",
            "location": "location",
            "year":     "year"
        }
        key = col_map.get(col, col)

        # Toggle sort direction for this column
        ascending = self._sort_ascending.get(col, True)
        self._sort_ascending[col] = not ascending  # Flip for next click

        # ── Sort using the _sort_key helper for numeric-aware sorting ──
        self.games.sort(
            key=lambda g: _sort_key(g, key),
            reverse=not ascending
        )

        # Update column heading to show sort direction arrow
        for c in col_map:
            heading_text = {
                "week": "Week", "date": "Date", "away": "Away Team",
                "home": "Home Team", "time": "Time",
                "location": "Location", "year": "Season"
            }[c]
            if c == col:
                arrow = " ▲" if ascending else " ▼"
                self.tree.heading(c, text=heading_text + arrow)
            else:
                self.tree.heading(c, text=heading_text)

        self.refresh_schedule_view()
        direction = "ascending" if ascending else "descending"
        self.update_status(f"Sorted by {col} ({direction})")

    # ─────────────────────────────────────────
    # File Operations
    # ─────────────────────────────────────────

    def _save_and_refresh(self, msg=""):
        """Save to file and refresh everything."""
        save_games(self.save_file, self.games)
        self.refresh_schedule_view()
        self.refresh_filter_options()
        self.update_status(msg + f" | Saved to '{self.save_file}'")

    def save_now(self):
        save_games(self.save_file, self.games)
        self.update_status(f"Saved {len(self.games)} game(s) to '{self.save_file}'")

    def save_as(self):
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
        path = filedialog.askopenfilename(
            filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")],
            title="Open Schedule File"
        )
        if path:
            self.save_file = path
            self.games     = load_games(self.save_file)
            self.file_label.config(text=f"File: {self.save_file}")
            self.refresh_schedule_view()
            self.refresh_filter_options()
            self.update_status(
                f"Opened '{self.save_file}' | {len(self.games)} game(s) loaded"
            )

    def new_schedule(self):
        if messagebox.askyesno("New Schedule",
                               "Start a new schedule? Unsaved changes will be lost."):
            self.games     = []
            self.save_file = DEFAULT_SAVE_FILE
            self.file_label.config(text=f"File: {self.save_file}")
            self.refresh_schedule_view()
            self.refresh_filter_options()
            self.clear_form()
            self.update_status("New schedule started.")

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
                # Export sorted by year then week numerically
                for g in sorted(
                    self.games,
                    key=lambda x: (int(x.get("year", 0)), int(x.get("week", 0)))
                ):
                    writer.writerow(g)
            self.update_status(f"Exported {len(self.games)} game(s) to '{path}'")

    # ─────────────────────────────────────────
    # Utility
    # ─────────────────────────────────────────

    def update_status(self, msg):
        self.status_var.set(f"  {msg}")

    def show_about(self):
        messagebox.showinfo(
            "About NFL Schedule Builder",
            "🏈 NFL Schedule Builder\n\n"
            "Build your NFL season schedule with ease.\n\n"
            "Features:\n"
            "  • Searchable team dropdowns\n"
            "  • Filter by team AND week\n"
            "  • Click outside to close dropdowns\n"
            "  • Numeric week & year sorting\n"
            "  • Toggle ascending/descending sort\n"
            "  • Live search across all fields\n"
            "  • Active filter indicator\n"
            "  • Add, edit, delete games\n"
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