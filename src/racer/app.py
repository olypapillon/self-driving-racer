"""The game window and its main loop."""

import asyncio
import random

import pygame

from .drivers import ALGORITHMS
from .ghost import Ghost, load_ghost, save_ghost
from .hud import draw_countdown, draw_hud, draw_results
from .minimap import build_minimap, draw_minimap, minimap_point
from .panels import (
    build_control_buttons,
    button_at,
    draw_control_panel,
    draw_leaderboard_panel,
    load_leaderboard,
    load_your_best,
    record_your_finish,
    save_your_best,
)
from .race import Car, build_race, update_race
from .render import build_trees, draw_road
from .settings import (
    BOOST_COLORS,
    CAMERA_HEIGHT,
    CAR_SHADOW_HEIGHT,
    CAR_SHADOW_VERTICAL_POSITION,
    COUNTDOWN_FONT_SIZE,
    DRIVER_CHOICES,
    FIXED_STEP,
    FPS,
    GHOST_COLOR,
    HUD_FONT_SIZE,
    HUMAN,
    IN_BROWSER,
    MUD_COLORS,
    PANEL_FONT_SIZE,
    PANEL_SMALL_FONT_SIZE,
    PANEL_TITLE_FONT_SIZE,
    PLAYER_CAR_BOTTOM_MARGIN,
    PLAYER_CAR_HEIGHT,
    PLAYER_CAR_SWAY,
    PLAYER_CAR_WIDTH,
    PLAYER_Z_OFFSET,
    RACE_MODES,
    RESULTS_FONT_SIZE,
    ROOT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SEGMENT_LENGTH,
    SIDE_PANEL_WIDTH,
    SIM_SPEEDS,
    SKY_PARALLAX_SPEED,
    STEERING_ANIMATION_RESPONSE,
    STEERING_SPRITE_THRESHOLD,
    TRACK_FEATURES,
    WINDOW_HEIGHT,
    WINDOW_WIDTH,
)
from .sprites import build_ghost_image, build_sky, build_tree_image
from .track import build_track, road_curve_at, road_elevation_at


async def main():
    """The game loop. It is async so the browser build (pygbag) can hand
    control back to the page once per frame; on the desktop it runs the same."""
    pygame.init()
    clock = pygame.time.Clock()
    window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    # The race view: drawing to it lands between the two side panels.
    screen = window.subsurface((SIDE_PANEL_WIDTH, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(
        "Self-Driving Racer | 1-7: who drives | M: battle / time trial"
        " | F: fast-forward | Tab: take over | R: restart"
    )

    car_path = ROOT / "assets" / "car-rear.png"
    car_image = pygame.image.load(car_path).convert_alpha()
    car_image = pygame.transform.smoothscale(
        car_image, (PLAYER_CAR_WIDTH, PLAYER_CAR_HEIGHT)
    )
    turning_car_path = (
        ROOT
        / "assets"
        / "car-rear-turn-left-subtle.png"
    )
    car_turn_left = pygame.image.load(turning_car_path).convert_alpha()
    car_turn_left = pygame.transform.smoothscale(
        car_turn_left, (PLAYER_CAR_WIDTH, PLAYER_CAR_HEIGHT)
    )
    car_turn_right = pygame.transform.flip(car_turn_left, True, False)
    car_rect = car_image.get_rect(
        midbottom=(
            SCREEN_WIDTH // 2,
            SCREEN_HEIGHT - PLAYER_CAR_BOTTOM_MARGIN,
        )
    )

    car_shadow = pygame.Surface((PLAYER_CAR_WIDTH, CAR_SHADOW_HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(
        car_shadow,
        (0, 0, 0, 45),
        (0, 0, PLAYER_CAR_WIDTH, CAR_SHADOW_HEIGHT),
    )
    pygame.draw.ellipse(
        car_shadow,
        (0, 0, 0, 90),
        (30, 10, PLAYER_CAR_WIDTH - 60, CAR_SHADOW_HEIGHT - 20),
    )
    car_shadow_rect = car_shadow.get_rect(
        center=(
            car_rect.centerx,
            car_rect.top + round(car_rect.height * CAR_SHADOW_VERTICAL_POSITION),
        )
    )

    sky = build_sky()
    track = build_track()
    track_length = len(track) * SEGMENT_LENGTH
    minimap, minimap_path = build_minimap(track)
    for kind, first, count, _ in TRACK_FEATURES:
        middle = (first + count / 2) * SEGMENT_LENGTH
        color = BOOST_COLORS[0] if kind == "boost" else MUD_COLORS[0]
        pygame.draw.circle(minimap, color, minimap_point(minimap_path, 0, 0, middle), 4)
    trees = build_trees(track)
    tree_image = build_tree_image()
    algorithm_index = ALGORITHMS.index("MPC Planner")
    mode_index = 0
    race = build_race(car_image, track, DRIVER_CHOICES[algorithm_index], RACE_MODES[mode_index])
    ghost = load_ghost()
    ghost_image = build_ghost_image(car_image)
    ghost_car = Car(
        name="Ghost", driver="ghost", distance=0.0, x=0.0, mass=1.0, size=1.0,
        color=GHOST_COLOR, image=ghost_image, rng=random.Random(0),
    )
    autopilot = True
    sim_speed_index = 0
    leader_checked = None
    sky_offset = 0.0
    visual_steering = 0.0
    accumulator = 0.0
    hud_font = pygame.font.Font(None, HUD_FONT_SIZE)
    countdown_font = pygame.font.Font(None, COUNTDOWN_FONT_SIZE)
    results_font = pygame.font.Font(None, RESULTS_FONT_SIZE)
    panel_fonts = (
        pygame.font.Font(None, PANEL_TITLE_FONT_SIZE),
        pygame.font.Font(None, PANEL_FONT_SIZE),
        pygame.font.Font(None, PANEL_SMALL_FONT_SIZE),
    )
    control_buttons = build_control_buttons()
    leaderboard = load_leaderboard()
    your_best = load_your_best()
    # The race you are driving by hand from the start, if any: only those count
    # for your leaderboard entry (taking over or handing back with Tab doesn't).
    race_by_hand = None
    running = True

    while running:
        # tick() sleeps, and on macOS the sleep overshoots unevenly; some frames
        # then run no physics step and others two, which reads as jumping.
        # tick_busy_loop() waits precisely at the cost of a little CPU.
        # In the browser a busy loop would freeze the page, so use tick().
        if IN_BROWSER:
            frame_time = min(clock.tick(FPS) / 1000, 0.25)
        else:
            frame_time = min(clock.tick_busy_loop(FPS) / 1000, 0.25)
        sim_speed = SIM_SPEEDS[sim_speed_index]
        accumulator += frame_time * sim_speed

        for event in pygame.event.get():
            # Keys and panel clicks both become an (action, value) pair.
            command = None
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                command = button_at(control_buttons, event.pos)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_TAB:
                    command = ("drive", None)
                elif event.key == pygame.K_f:
                    command = ("speed", (sim_speed_index + 1) % len(SIM_SPEEDS))
                elif pygame.K_1 <= event.key < pygame.K_1 + len(DRIVER_CHOICES):
                    command = ("algorithm", event.key - pygame.K_1)
                elif event.key == pygame.K_m:
                    command = ("mode", (mode_index + 1) % len(RACE_MODES))
                elif event.key == pygame.K_r:
                    command = ("restart", None)
            if command is None:
                continue

            action, value = command
            new_race = False
            if action == "drive":
                autopilot = not autopilot
                race_by_hand = None
                if not autopilot:
                    # Fast-forward is for watching the AI; you drive at 1x.
                    sim_speed_index = 0
            elif action == "speed" and autopilot:
                sim_speed_index = value
            elif action == "algorithm":
                algorithm_index = value
                new_race = True
            elif action == "mode":
                new_race = value != mode_index
                mode_index = value
            elif action == "restart":
                new_race = True
            if new_race:
                choice = DRIVER_CHOICES[algorithm_index]
                race = build_race(car_image, track, choice, RACE_MODES[mode_index])
                autopilot = choice != HUMAN
                if not autopilot:
                    sim_speed_index = 0  # you drive at 1x
                race_by_hand = None if autopilot else race
                sky_offset = 0.0
                visual_steering = 0.0

        keys = pygame.key.get_pressed()
        steering = int(keys[pygame.K_d] or keys[pygame.K_RIGHT]) - int(
            keys[pygame.K_a] or keys[pygame.K_LEFT]
        )
        throttle = int(keys[pygame.K_w] or keys[pygame.K_UP])
        brake = int(keys[pygame.K_s] or keys[pygame.K_DOWN])
        player = race.player
        player.name = player.algorithm if autopilot else "You"

        while accumulator >= FIXED_STEP:
            controls = None if autopilot else (steering, throttle, brake)
            update_race(race, track, track_length, controls, FIXED_STEP)
            road_curve = road_curve_at(track, player.distance % track_length)
            sky_offset += SKY_PARALLAX_SPEED * road_curve * player.speed * FIXED_STEP
            animation_target = player.steering if player.speed > 0 else 0
            animation_blend = min(1.0, STEERING_ANIMATION_RESPONSE * FIXED_STEP)
            visual_steering += (animation_target - visual_steering) * animation_blend
            accumulator -= FIXED_STEP

        # A finished run that beats the ghost becomes the new ghost. Checked
        # once per race; the recording stopped at the finish line.
        if player.finish_time is not None and leader_checked is not race:
            leader_checked = race
            if race_by_hand is race and record_your_finish(your_best, race):
                save_your_best(your_best)
            if ghost is None or player.finish_time < ghost.time:
                name = race.player.algorithm if autopilot else "You"
                ghost = Ghost(name, player.finish_time, list(race.recording))
                save_ghost(ghost)

        frame = ghost.at(race.steps) if ghost is not None else None
        ghost_visible = frame is not None
        if ghost_visible:
            ghost_car.distance, ghost_car.x = frame

        # The camera sits PLAYER_Z_OFFSET behind the car it follows.
        position = (player.distance - PLAYER_Z_OFFSET) % track_length
        camera_y = road_elevation_at(track, position) + CAMERA_HEIGHT
        draw_road(
            screen,
            track,
            trees,
            tree_image,
            race.cars[1:] + ([ghost_car] if ghost_visible else []),
            position,
            player.x,
            camera_y,
            sky,
            sky_offset,
            race.features,
        )
        car_center_x = SCREEN_WIDTH // 2 + round(visual_steering * PLAYER_CAR_SWAY)
        car_shadow_rect.centerx = car_center_x
        if visual_steering < -STEERING_SPRITE_THRESHOLD:
            rendered_car = car_turn_left
        elif visual_steering > STEERING_SPRITE_THRESHOLD:
            rendered_car = car_turn_right
        else:
            rendered_car = car_image
        rendered_car_rect = rendered_car.get_rect(
            midbottom=(
                car_center_x,
                SCREEN_HEIGHT - PLAYER_CAR_BOTTOM_MARGIN,
            )
        )
        screen.blit(car_shadow, car_shadow_rect)
        screen.blit(rendered_car, rendered_car_rect)
        draw_minimap(
            screen, minimap, minimap_path, race, track_length,
            ghost_car if ghost_visible else None,
        )
        draw_hud(screen, hud_font, race, ghost, autopilot, sim_speed)
        draw_countdown(screen, countdown_font, race)
        if player.finish_time is not None:
            draw_results(screen, results_font, race)
        panel_state = {
            "algorithm": algorithm_index,
            "mode": mode_index,
            "speed": sim_speed_index,
            "autopilot": autopilot,
        }
        mouse = pygame.mouse.get_pos()
        draw_control_panel(window, panel_fonts, control_buttons, panel_state, mouse)
        draw_leaderboard_panel(
            window, panel_fonts, leaderboard, your_best, DRIVER_CHOICES[algorithm_index]
        )
        pygame.display.flip()
        await asyncio.sleep(0)

    pygame.quit()
