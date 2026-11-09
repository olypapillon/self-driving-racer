"""The side panels: who drives and race controls on the left, the leaderboard
on the right, and your own best times."""

import json

import pygame

from .drivers import ALGORITHMS
from .race import standings
from .settings import (
    ALGORITHM_COLORS,
    BUTTON_COLOR,
    BUTTON_DISABLED_TEXT,
    BUTTON_GAP,
    BUTTON_HEIGHT,
    BUTTON_HOVER_COLOR,
    BUTTON_SELECTED_COLOR,
    DRIVER_CHOICES,
    HUD_BEST_COLOR,
    HUD_MUTED_COLOR,
    HUMAN,
    IN_BROWSER,
    LEADERBOARD_PATH,
    PANEL_BACKGROUND,
    PANEL_MARGIN,
    RACE_MODES,
    SIDE_PANEL_WIDTH,
    SIM_SPEEDS,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
    YOUR_BEST_KEY,
    YOUR_BEST_PATH,
)


def load_leaderboard():
    """Rows of leaderboard.json (written by benchmark.py), or [] if missing."""
    try:
        return json.loads(LEADERBOARD_PATH.read_text())["algorithms"]
    except (OSError, ValueError, KeyError):
        return []


def browser_storage():
    """The page's localStorage in the browser build, else None."""
    if not IN_BROWSER:
        return None
    try:
        import platform  # pygbag's module, with the page's JavaScript window

        return platform.window.localStorage
    except Exception:
        return None


def load_your_best():
    """{"time_trial": seconds, "battle_place": place}; either may be missing."""
    try:
        storage = browser_storage()
        text = storage.getItem(YOUR_BEST_KEY) if storage is not None else YOUR_BEST_PATH.read_text()
        best = json.loads(text) if text else {}
        return best if isinstance(best, dict) else {}
    except Exception:
        return {}


def save_your_best(best):
    try:
        text = json.dumps(best)
        storage = browser_storage()
        if storage is not None:
            storage.setItem(YOUR_BEST_KEY, text)
        else:
            YOUR_BEST_PATH.write_text(text)
    except Exception:
        pass  # keeping the record is nice to have, never worth a crash


def record_your_finish(best, race):
    """Fold a hand-driven finish into ``best``; True if it improved."""
    player = race.player
    improved = False
    if race.mode == "Time trial":
        if best.get("time_trial") is None or player.finish_time < best["time_trial"]:
            best["time_trial"] = round(player.finish_time, 2)
            improved = True
    else:
        place = standings(race).index(player) + 1
        if best.get("battle_place") is None or place < best["battle_place"]:
            best["battle_place"] = place
            improved = True
    return improved


def build_control_buttons():
    """Clickable buttons of the left panel: a list of (rect, action, value).

    The section labels sit in the gaps left above each group; see
    CONTROL_SECTIONS for their heights.
    """
    left, width = PANEL_MARGIN, SIDE_PANEL_WIDTH - 2 * PANEL_MARGIN
    buttons = []
    y = CONTROL_SECTIONS["Who drives"]
    for index in range(len(DRIVER_CHOICES)):
        buttons.append((pygame.Rect(left, y, width, BUTTON_HEIGHT), "algorithm", index))
        y += BUTTON_HEIGHT + BUTTON_GAP

    def row(top, action, count):
        cell = (width - BUTTON_GAP * (count - 1)) / count
        for index in range(count):
            rect = pygame.Rect(round(left + index * (cell + BUTTON_GAP)), top, round(cell), BUTTON_HEIGHT)
            buttons.append((rect, action, index))

    row(CONTROL_SECTIONS["Race"], "mode", len(RACE_MODES))
    row(CONTROL_SECTIONS["Speed"], "speed", len(SIM_SPEEDS))
    y = CONTROL_SECTIONS["Speed"] + BUTTON_HEIGHT + 2 * BUTTON_GAP
    buttons.append((pygame.Rect(left, y, width, BUTTON_HEIGHT), "restart", None))
    return buttons


# Top of each button group in the left panel; its label goes just above it.
CONTROL_SECTIONS = {"Who drives": 120, "Race": 500, "Speed": 590}


def button_at(buttons, position):
    """The (action, value) of the button under a window position, else None."""
    for rect, action, value in buttons:
        if rect.collidepoint(position):
            return action, value
    return None


def draw_button(window, rect, font, label, hovered, selected, enabled=True, accent=None):
    if selected:
        color = BUTTON_SELECTED_COLOR
    elif hovered and enabled:
        color = BUTTON_HOVER_COLOR
    else:
        color = BUTTON_COLOR
    pygame.draw.rect(window, color, rect, border_radius=8)
    if selected:
        pygame.draw.rect(window, accent or HUD_BEST_COLOR, rect, 2, border_radius=8)
    text = font.render(label, True, "white" if enabled else BUTTON_DISABLED_TEXT)
    window.blit(text, text.get_rect(center=rect.center))


def draw_control_panel(window, fonts, buttons, state, mouse):
    """Left panel: pick the algorithm, the race mode, the speed and the driver."""
    title_font, font, small_font = fonts
    pygame.draw.rect(window, PANEL_BACKGROUND, (0, 0, SIDE_PANEL_WIDTH, WINDOW_HEIGHT))
    window.blit(title_font.render("Self-Driving Racer", True, HUD_BEST_COLOR), (PANEL_MARGIN, 26))
    window.blit(
        small_font.render("Watch an algorithm, or race them", True, HUD_MUTED_COLOR),
        (PANEL_MARGIN, 64),
    )
    for label, top in CONTROL_SECTIONS.items():
        window.blit(small_font.render(label.upper(), True, HUD_MUTED_COLOR), (PANEL_MARGIN, top - 24))

    for rect, action, value in buttons:
        hovered = rect.collidepoint(mouse)
        if action == "algorithm":
            name = DRIVER_CHOICES[value]
            accent = ALGORITHM_COLORS.get(name, "white")
            selected = value == state["algorithm"]
            pygame.draw.rect(window, BUTTON_SELECTED_COLOR if selected else (
                BUTTON_HOVER_COLOR if hovered else BUTTON_COLOR), rect, border_radius=8)
            if selected:
                pygame.draw.rect(window, accent, rect, 2, border_radius=8)
            pygame.draw.circle(window, accent, (rect.left + 20, rect.centery), 7)
            window.blit(font.render(name, True, "white"), (rect.left + 38, rect.centery - 9))
            key = small_font.render(str(value + 1), True, HUD_MUTED_COLOR)
            window.blit(key, key.get_rect(midright=(rect.right - 14, rect.centery)))
        elif action == "mode":
            draw_button(window, rect, font, RACE_MODES[value], hovered, value == state["mode"])
        elif action == "speed":
            enabled = state["autopilot"]
            selected = enabled and value == state["speed"]
            draw_button(window, rect, font, f"{SIM_SPEEDS[value]}x", hovered, selected, enabled)
        elif action == "restart":
            draw_button(window, rect, font, "Restart race", hovered, False)

    hints = [
        "Keys: 1-7 who drives, M race,",
        "F speed, R restart.",
        "You: drive with arrows or WASD.",
        "Tab takes over (or hands back)",
        "the car mid-race.",
        "",
        "Fast-forward only changes how",
        "quickly the race is shown.",
    ]
    y = WINDOW_HEIGHT - PANEL_MARGIN - len(hints) * small_font.get_linesize()
    for line in hints:
        window.blit(small_font.render(line, True, HUD_MUTED_COLOR), (PANEL_MARGIN, y))
        y += small_font.get_linesize()


def leaderboard_rows(leaderboard, your_best):
    """The benchmark's rows plus yours, as (time or None, name, line 1, line 2).

    Algorithms are ranked by their average time-trial lap; you by your best
    lap. Without a lap yet you go to the bottom.
    """
    rows = []
    for entry in leaderboard:
        details = (
            f"best {entry['trial_best']:.2f} s  ·  {entry['trial_finished']} finished"
            if entry["trial_best"] is not None
            else f"{entry['trial_finished']} finished"
        )
        battle = f"battle: avg {entry['battle_avg_place']}  ·  {entry['battle_wins']} wins"
        rows.append((entry["trial_mean"], entry["name"], details, battle))
    trial = your_best.get("time_trial")
    place = your_best.get("battle_place")
    rows.append((
        trial,
        HUMAN,
        "your best time-trial lap" if trial is not None else "Pick You, then Time trial,",
        f"battle: best place {place}/{len(ALGORITHMS) + 1}" if place is not None
        else ("no battle finished yet" if trial is not None else "to set your time"),
    ))
    rows.sort(key=lambda row: (row[0] is None, row[0] or 0.0))
    return rows


def draw_leaderboard_panel(window, fonts, leaderboard, your_best, selected_name):
    """Right panel: the benchmark's ranking plus your best, the chosen driver highlighted."""
    title_font, font, small_font = fonts
    left = WINDOW_WIDTH - SIDE_PANEL_WIDTH
    pygame.draw.rect(window, PANEL_BACKGROUND, (left, 0, SIDE_PANEL_WIDTH, WINDOW_HEIGHT))
    x = left + PANEL_MARGIN
    width = SIDE_PANEL_WIDTH - 2 * PANEL_MARGIN
    window.blit(title_font.render("Leaderboard", True, HUD_BEST_COLOR), (x, 26))
    window.blit(
        small_font.render("Ranked by time-trial lap time", True, HUD_MUTED_COLOR), (x, 64)
    )

    row_height = 86
    y = 100
    for place, (time, name, details, battle) in enumerate(
        leaderboard_rows(leaderboard, your_best), start=1
    ):
        accent = ALGORITHM_COLORS.get(name, "white")
        rect = pygame.Rect(x, y, width, row_height - BUTTON_GAP)
        selected = name == selected_name
        pygame.draw.rect(window, BUTTON_SELECTED_COLOR if selected else BUTTON_COLOR, rect, border_radius=8)
        if selected:
            pygame.draw.rect(window, accent, rect, 2, border_radius=8)
        rank = title_font.render(str(place) if time is not None else "-", True, accent)
        window.blit(rank, rank.get_rect(midleft=(rect.left + 14, rect.top + 24)))
        window.blit(font.render(name, True, "white"), (rect.left + 46, rect.top + 14))
        time_text = font.render(f"{time:.2f} s" if time is not None else "--", True, accent)
        window.blit(time_text, time_text.get_rect(topright=(rect.right - 12, rect.top + 14)))
        window.blit(small_font.render(details, True, HUD_MUTED_COLOR), (rect.left + 46, rect.top + 40))
        window.blit(small_font.render(battle, True, HUD_MUTED_COLOR), (rect.left + 46, rect.top + 58))
        y += row_height

    notes = [
        "Algorithms: average of 5 time-trial",
        "seeds; battle over 12 seeds.",
        "You: your best lap, kept in this",
        "browser.",
    ]
    y += 6
    for line in notes:
        window.blit(small_font.render(line, True, HUD_MUTED_COLOR), (x, y))
        y += small_font.get_linesize()
