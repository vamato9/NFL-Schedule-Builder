# NFL Schedule Builder Tool
# Allows user to input known matchups and dates, then displays full schedule per team

from datetime import datetime
from collections import defaultdict

# ─────────────────────────────────────────────
# Data Store
# ─────────────────────────────────────────────

# List to store all games
games = []

# ─────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────

def add_game(week, date_str, home_team, away_team, time_str="TBD", location="TBD"):
    """
    Add a game to the schedule.
    :param week: NFL week number (int)
    :param date_str: Date string in MM/DD/YYYY format
    :param home_team: Home team name (str)
    :param away_team: Away team name (str)
    :param time_str: Game time as string (e.g. '1:00 PM ET')
    :param location: Stadium or city name
    """
    try:
        # Parse date if provided, otherwise mark as TBD
        if date_str.upper() == "TBD":
            game_date = "TBD"
        else:
            game_date = datetime.strptime(date_str, "%m/%d/%Y").strftime("%A, %B %d, %Y")
    except ValueError:
        print(f"  [!] Invalid date format: '{date_str}'. Use MM/DD/YYYY. Game not added.")
        return

    # Build game dictionary
    game = {
        "week": week,
        "date": game_date,
        "home_team": home_team.strip().title(),
        "away_team": away_team.strip().title(),
        "time": time_str,
        "location": location
    }

    games.append(game)
    print(f"  [+] Game added: Week {week} | {away_team} @ {home_team} | {game_date}")


def view_team_schedule(team_name):
    """
    Display the full schedule for a specific team.
    :param team_name: The team name to search for
    """
    team_name = team_name.strip().title()

    # Filter games where the team is home or away
    team_games = [
        g for g in games
        if g["home_team"] == team_name or g["away_team"] == team_name
    ]

    if not team_games:
        print(f"\n  [!] No games found for '{team_name}'.")
        return

    # Sort by week number
    team_games.sort(key=lambda x: x["week"])

    print(f"\n{'='*60}")
    print(f"  📅 Schedule for: {team_name}")
    print(f"{'='*60}")
    print(f"  {'Week':<6} {'Date':<30} {'Matchup':<35} {'Time':<15} {'Location'}")
    print(f"  {'-'*110}")

    for g in team_games:
        # Determine home/away label
        if g["home_team"] == team_name:
            opponent = f"vs {g['away_team']} (Home)"
        else:
            opponent = f"@ {g['home_team']} (Away)"

        print(f"  {g['week']:<6} {g['date']:<30} {opponent:<35} {g['time']:<15} {g['location']}")

    print(f"{'='*60}")
    print(f"  Total games scheduled: {len(team_games)}")


def view_all_teams():
    """
    Display a list of all teams currently in the schedule.
    """
    # Collect all unique team names
    teams = set()
    for g in games:
        teams.add(g["home_team"])
        teams.add(g["away_team"])

    if not teams:
        print("\n  [!] No teams found. Add some games first.")
        return

    print(f"\n  Teams in schedule ({len(teams)} total):")
    for t in sorted(teams):
        print(f"    - {t}")


def view_full_schedule_by_week():
    """
    Display all games sorted by week.
    """
    if not games:
        print("\n  [!] No games added yet.")
        return

    # Group by week
    by_week = defaultdict(list)
    for g in games:
        by_week[g["week"]].append(g)

    print(f"\n{'='*60}")
    print("  📆 Full NFL Schedule by Week")
    print(f"{'='*60}")

    for week in sorted(by_week.keys()):
        print(f"\n  --- Week {week} ---")
        for g in by_week[week]:
            print(f"    {g['away_team']} @ {g['home_team']} | {g['date']} | {g['time']} | {g['location']}")


def remove_game(week, home_team, away_team):
    """
    Remove a specific game from the schedule.
    :param week: Week number of the game
    :param home_team: Home team name
    :param away_team: Away team name
    """
    global games
    home_team = home_team.strip().title()
    away_team = away_team.strip().title()

    before = len(games)
    games = [
        g for g in games
        if not (g["week"] == week and g["home_team"] == home_team and g["away_team"] == away_team)
    ]
    after = len(games)

    if before > after:
        print(f"  [-] Removed: Week {week} | {away_team} @ {home_team}")
    else:
        print(f"  [!] Game not found: Week {week} | {away_team} @ {home_team}")


# ─────────────────────────────────────────────
# Interactive Menu
# ─────────────────────────────────────────────

def main_menu():
    """
    Main interactive menu loop for the NFL Schedule Builder.
    """
    print("\n" + "="*60)
    print("  🏈 NFL Schedule Builder")
    print("="*60)

    while True:
        print("\n  Options:")
        print("    1. Add a game")
        print("    2. View schedule for a team")
        print("    3. View all teams")
        print("    4. View full schedule by week")
        print("    5. Remove a game")
        print("    6. Exit")

        choice = input("\n  Enter choice (1-6): ").strip()

        if choice == "1":
            # ── Add a game ──
            print("\n  -- Add a Game --")
            try:
                week     = int(input("  Week number: ").strip())
                date_str = input("  Date (MM/DD/YYYY or TBD): ").strip()
                home     = input("  Home team name: ").strip()
                away     = input("  Away team name: ").strip()
                time_str = input("  Game time (e.g. 1:00 PM ET or TBD): ").strip() or "TBD"
                location = input("  Location/Stadium (or TBD): ").strip() or "TBD"
                add_game(week, date_str, home, away, time_str, location)
            except ValueError:
                print("  [!] Invalid week number. Please enter an integer.")

        elif choice == "2":
            # ── View team schedule ──
            team = input("\n  Enter team name: ").strip()
            view_team_schedule(team)

        elif choice == "3":
            # ── View all teams ──
            view_all_teams()

        elif choice == "4":
            # ── View full schedule by week ──
            view_full_schedule_by_week()

        elif choice == "5":
            # ── Remove a game ──
            print("\n  -- Remove a Game --")
            try:
                week = int(input("  Week number: ").strip())
                home = input("  Home team name: ").strip()
                away = input("  Away team name: ").strip()
                remove_game(week, home, away)
            except ValueError:
                print("  [!] Invalid week number.")

        elif choice == "6":
            print("\n  Goodbye! 🏈")
            break

        else:
            print("  [!] Invalid choice. Please enter 1-6.")


# ─────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────

if __name__ == "__main__":
    main_menu()