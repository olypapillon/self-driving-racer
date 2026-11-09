"""Text drawn over the race view: driver panel, countdown and results."""

import math

import pygame

from .race import standings
from .settings import (
    GHOST_COLOR,
    GO_DISPLAY_SECONDS,
    HUD_BEST_COLOR,
    HUD_MUTED_COLOR,
    HUD_PADDING,
    MINIMAP_BACKGROUND,
    MINIMAP_MARGIN,
    RESULTS_PADDING,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


def format_lap_time(seconds):
    if seconds is None:
        return "--:--.--"
    minutes, seconds = divmod(seconds, 60)
    return f"{int(minutes)}:{seconds:05.2f}"


def draw_hud(screen, font, race, ghost, autopilot, sim_speed):
    """Driver, position, time and the gap to the ghost, opposite the mini map."""
    player = race.player
    order = standings(race)
    # Everything is timed on the race clock from GO, the same clock the ghost
    # was recorded on, so the two can be compared directly.
    race_time = player.finish_time if player.finish_time is not None else race.clock
    driver = player.algorithm if autopilot else "You (keyboard)"
    lines = [
        (driver + (f"   >> {sim_speed}x" if sim_speed > 1 else ""), HUD_BEST_COLOR),
        (race.mode, HUD_MUTED_COLOR),
        (f"Pos  {order.index(player) + 1}/{len(order)}", "white"),
        (f"Time {format_lap_time(race_time)}", "white"),
    ]
    if ghost is not None:
        lines.append((f"Ghost {ghost.name} {format_lap_time(ghost.time)}", GHOST_COLOR))
        if race.clock > 0:
            # Positive: you reached this point later than the ghost did.
            if player.finish_time is not None:
                gap = player.finish_time - ghost.time
            else:
                gap = race.clock - ghost.time_at(player.distance)
            gap_color = (120, 230, 120) if gap <= 0 else (240, 110, 110)
            lines.append((f"Gap  {gap:+.2f} s", gap_color))
    rendered = [font.render(text, True, color) for text, color in lines]
    line_height = font.get_linesize()
    width = max(text.get_width() for text in rendered) + 2 * HUD_PADDING
    height = line_height * len(rendered) + 2 * HUD_PADDING

    panel = pygame.Rect(MINIMAP_MARGIN, MINIMAP_MARGIN, width, height)
    pygame.draw.rect(screen, MINIMAP_BACKGROUND, panel, border_radius=HUD_PADDING)
    for index, text in enumerate(rendered):
        screen.blit(
            text,
            (panel.left + HUD_PADDING, panel.top + HUD_PADDING + index * line_height),
        )


def draw_countdown(screen, font, race):
    """3, 2, 1 over the grid, then GO! for a moment after the start."""
    if race.countdown > 0:
        text, color = str(math.ceil(race.countdown)), "white"
    elif race.clock < GO_DISPLAY_SECONDS:
        text, color = "GO!", HUD_BEST_COLOR
    else:
        return
    shadow = font.render(text, True, "black")
    label = font.render(text, True, color)
    center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 3)
    screen.blit(shadow, shadow.get_rect(center=(center[0] + 4, center[1] + 4)))
    screen.blit(label, label.get_rect(center=center))


def draw_results(screen, font, race):
    """Finishing order, filled in live as the other racers cross the line."""
    rows = []
    for place, car in enumerate(standings(race), start=1):
        result = (
            format_lap_time(car.finish_time)
            if car.finish_time is not None
            else "racing"
        )
        color = "white" if car is race.player else HUD_MUTED_COLOR
        name = font.render(f"{place}. {car.name}", True, color)
        rows.append((name, font.render(result, True, color)))
    title = font.render("Results", True, HUD_BEST_COLOR)
    footer = font.render("R restart  |  Tab drive yourself", True, HUD_MUTED_COLOR)

    # Names and times in two columns; the font is not monospaced.
    name_width = max(name.get_width() for name, _ in rows)
    time_width = max(time.get_width() for _, time in rows)
    line_height = font.get_linesize()
    width = max(name_width + RESULTS_PADDING + time_width, footer.get_width())
    height = line_height * (len(rows) + 2)
    panel = pygame.Rect(0, 0, width + 2 * RESULTS_PADDING, height + 2 * RESULTS_PADDING)
    panel.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 60)
    pygame.draw.rect(screen, MINIMAP_BACKGROUND, panel, border_radius=HUD_PADDING)

    left = panel.left + RESULTS_PADDING
    top = panel.top + RESULTS_PADDING
    screen.blit(title, (left, top))
    for index, (name, time) in enumerate(rows, start=1):
        y = top + index * line_height
        screen.blit(name, (left, y))
        screen.blit(time, (left + width - time.get_width(), y))
    screen.blit(footer, (left, top + (len(rows) + 1) * line_height))
