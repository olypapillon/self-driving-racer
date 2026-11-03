import pygame
import math
from pathlib import Path

pygame.init()
clock = pygame.time.Clock()
dt = 0
screen = pygame.display.set_mode((1100, 900))
track_center = (screen.width // 2, screen.height // 2)
track_radius = 325
track_width = 125
track_inner_radius = track_radius - track_width
checkpoint_thickness = 12
center_x, center_y = track_center
finish_checkpoint = pygame.Rect(
    center_x - track_radius,
    center_y - checkpoint_thickness // 2,
    track_width,
    checkpoint_thickness,
)
checkpoints = [
    pygame.Rect(
        center_x - checkpoint_thickness // 2,
        center_y - track_radius,
        checkpoint_thickness,
        track_width,
    ),
    pygame.Rect(
        center_x + track_inner_radius,
        center_y - checkpoint_thickness // 2,
        track_width,
        checkpoint_thickness,
    ),
    pygame.Rect(
        center_x - checkpoint_thickness // 2,
        center_y + track_inner_radius,
        checkpoint_thickness,
        track_width,
    ),
]
player_car = pygame.Rect(screen.width / 2, screen.height / 2, 50, 50)
player_car.center = (
    track_center[0] - track_radius + track_width // 2,
    track_center[1],
)
car_sprite_path = Path(__file__).resolve().parent.parent / "assets" / "car.png"
car_sprite = pygame.image.load(car_sprite_path).convert_alpha()
car_sprite = pygame.transform.smoothscale(car_sprite, (28, 50))
car_position = pygame.Vector2(player_car.center)
car_speed = 0.0
car_heading = 0.0
next_checkpoint = 0
lap_count = 0
was_touching_finish = player_car.colliderect(finish_checkpoint)
lap_font = pygame.font.Font(None, 36)
finish_font = pygame.font.Font(None, 72)
race_time = 0.0
race_finished = False

ACCELERATION = 80
REVERSE_ACCELERATION = 80
BRAKING = 350
FRICTION = 50
GRASS_FRICTION = 250

MAX_FORWARD_SPEED = 450
MAX_REVERSE_SPEED = -150
GRASS_MAX_FORWARD_SPEED = 100
GRASS_MAX_REVERSE_SPEED = -50

TURN_SPEED = 140
HEADING_RETURN_SPEED = 180
TOTAL_LAPS = 3


def keyboard_driver():
    keys = pygame.key.get_pressed()
    throttle = float(keys[pygame.K_w])
    brake = float(keys[pygame.K_s])
    steering = float(keys[pygame.K_d]) - float(keys[pygame.K_a])
    return throttle, brake, steering


def main():
    print("Hello from self-driving-racer!")


if __name__ == "__main__":
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        throttle, brake, steering = keyboard_driver()

        if not race_finished:
            race_time += dt

        distance_from_center = car_position.distance_to(track_center)
        on_road = track_inner_radius <= distance_from_center <= track_radius
        current_friction = FRICTION if on_road else GRASS_FRICTION
        current_max_forward_speed = (
            MAX_FORWARD_SPEED if on_road else GRASS_MAX_FORWARD_SPEED
        )
        current_max_reverse_speed = (
            MAX_REVERSE_SPEED if on_road else GRASS_MAX_REVERSE_SPEED
        )

        if not race_finished:
            if throttle > 0:
                if car_speed < 0:
                    car_speed = min(0, car_speed + BRAKING * throttle * dt)
                else:
                    car_speed += ACCELERATION * throttle * dt
            elif brake > 0:
                if car_speed > 0:
                    car_speed = max(0, car_speed - BRAKING * brake * dt)
                else:
                    car_speed -= REVERSE_ACCELERATION * brake * dt
        else:
            car_speed = 0

        car_speed = max(
            current_max_reverse_speed,
            min(current_max_forward_speed, car_speed),
        )

        # Friction
        if throttle == 0 and brake == 0:
            if car_speed > 0:
                car_speed -= current_friction * dt
                car_speed = max(car_speed, 0)
            elif car_speed < 0:
                car_speed += current_friction * dt
                car_speed = min(car_speed, 0)

        # Heading and direction
        if steering:
            speed_ratio = min(abs(car_speed) / MAX_FORWARD_SPEED, 1.0)
            reverse_direction = 1 if car_speed > 0 else -1
            car_heading += (
                steering * TURN_SPEED * speed_ratio * reverse_direction * dt
            )

        car_heading %= 360

        angle = math.radians(car_heading - 90)
        direction_x = math.cos(angle)
        direction_y = math.sin(angle)

        # Move forward/backward along the car's heading
        car_position.x += direction_x * car_speed * dt
        car_position.y += direction_y * car_speed * dt

        half_width = player_car.width / 2
        half_height = player_car.height / 2
        car_position.x = max(half_width, min(screen.width - half_width, car_position.x))
        car_position.y = max(
            half_height, min(screen.height - half_height, car_position.y)
        )

        player_car.center = round(car_position.x), round(car_position.y)

        touching_finish = player_car.colliderect(finish_checkpoint)
        if not race_finished:
            if next_checkpoint < len(checkpoints) and player_car.colliderect(
                checkpoints[next_checkpoint]
            ):
                next_checkpoint += 1

            moving_up = direction_y * car_speed < 0
            if touching_finish and not was_touching_finish:
                if next_checkpoint == len(checkpoints) and moving_up:
                    lap_count += 1
                    next_checkpoint = 0
                    if lap_count >= TOTAL_LAPS:
                        race_finished = True
                        car_speed = 0
        was_touching_finish = touching_finish

        finish_y = track_center[1]
        outer_x = track_center[0] - track_radius
        finish_tile_size = 15

        # Draw the background and track first so the car appears on top.
        screen.fill("forestgreen")
        pygame.draw.circle(screen, "dimgray", track_center, track_radius, track_width)
        pygame.draw.circle(screen, "white", track_center, track_radius, 4)
        pygame.draw.circle(screen, "white", track_center, track_radius - track_width, 4)
        for row in range(2):
            for offset in range(0, track_width, finish_tile_size):
                color = (
                    "white" if (offset // finish_tile_size + row) % 2 == 0 else "black"
                )
                tile_width = min(finish_tile_size, track_width - offset)
                pygame.draw.rect(
                    screen,
                    color,
                    (
                        outer_x + offset,
                        finish_y - finish_tile_size + row * finish_tile_size,
                        tile_width,
                        finish_tile_size,
                    ),
                )
        pygame.draw.line(
            screen,
            "white",
            (outer_x + 2 * track_radius, finish_y),
            (track_center[0] + track_radius - track_width, finish_y),
            4,
        )
        pygame.draw.line(
            screen,
            "white",
            (track_center[0], track_center[1] + track_radius),
            (track_center[0], track_center[1] + track_radius - track_width),
            4,
        )

        pygame.draw.line(
            screen,
            "white",
            (track_center[0], track_center[1] - track_radius),
            (track_center[0], track_center[1] - track_radius + track_width),
            4,
        )

        rotated_car_sprite = pygame.transform.rotate(car_sprite, -car_heading)
        sprite_rect = rotated_car_sprite.get_rect(center=player_car.center)
        screen.blit(rotated_car_sprite, sprite_rect)
        minutes = int(race_time // 60)
        seconds = race_time % 60
        lap_text = lap_font.render(
            f"Laps: {lap_count}/{TOTAL_LAPS}", True, "white"
        )
        timer_text = lap_font.render(
            f"Time: {minutes:02}:{seconds:05.2f}", True, "white"
        )
        screen.blit(lap_text, (20, 20))
        screen.blit(timer_text, (20, 55))

        if race_finished:
            finish_text = finish_font.render("Race Finished!", True, "gold")
            final_time_text = lap_font.render(
                f"Final time: {minutes:02}:{seconds:05.2f}", True, "white"
            )
            finish_text_rect = finish_text.get_rect(
                center=(screen.width // 2, screen.height // 2 - 25)
            )
            final_time_rect = final_time_text.get_rect(
                center=(screen.width // 2, screen.height // 2 + 30)
            )
            finish_panel = finish_text_rect.union(final_time_rect).inflate(60, 50)
            pygame.draw.rect(screen, "black", finish_panel, border_radius=12)
            screen.blit(finish_text, finish_text_rect)
            screen.blit(final_time_text, final_time_rect)
        # nose = car_position + pygame.Vector2(direction_x, direction_y) * half_height
        # pygame.draw.line(screen, "white", car_position, nose, 4)

        pygame.display.flip()
        dt = clock.tick(60) / 1000
    pygame.quit()
