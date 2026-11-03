from pathlib import Path

from manim import (
    Arrow,
    Circle,
    Create,
    DashedLine,
    DOWN,
    FadeIn,
    FadeOut,
    Group,
    GrowArrow,
    ImageMobject,
    Indicate,
    LEFT,
    Line,
    Polygon,
    Rectangle,
    ReplacementTransform,
    RIGHT,
    RoundedRectangle,
    Scene,
    SurroundingRectangle,
    Text,
    Transform,
    UP,
    ValueTracker,
    VGroup,
    WHITE,
    Write,
    always_redraw,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CAR_IMAGE_PATH = PROJECT_ROOT / "assets" / "car-rear.png"

BACKGROUND = "#0B1020"
PANEL = "#151D32"
TEXT = "#ECF2FF"
MUTED = "#9FB0CF"
PLAYER = "#58A6FF"
UPDATE = "#F2CC60"
PROJECT = "#C297FF"
CURVE = "#FF8A65"
DRAW = "#63D297"
ROAD_LIGHT = "#565B66"
ROAD_DARK = "#444954"
GRASS = "#176B3A"
SKY = "#63B4D8"


def make_text(content, size=28, color=TEXT, weight="NORMAL"):
    return Text(content, font_size=size, color=color, weight=weight)


def make_heading(content, color=TEXT):
    heading = make_text(content, 35, color, "BOLD")
    heading.to_corner(UP + LEFT, buff=0.45).shift(DOWN * 0.58)
    return heading


def make_code_panel(lines, width=6.25, font_size=20):
    code_lines = VGroup(
        *[
            Text(line, font="Monospace", font_size=font_size, color=TEXT)
            for line in lines
        ]
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.15)
    panel = RoundedRectangle(
        width=width,
        height=code_lines.height + 0.52,
        corner_radius=0.14,
        stroke_color="#33415F",
        stroke_width=1.5,
        fill_color=PANEL,
        fill_opacity=1,
    )
    code_lines.move_to(panel).align_to(panel, LEFT).shift(RIGHT * 0.25)
    return VGroup(panel, code_lines)


def line_highlight(panel, index, color):
    return SurroundingRectangle(
        panel[1][index],
        buff=0.06,
        color=color,
        stroke_width=2,
        fill_color=color,
        fill_opacity=0.13,
    )


def make_perspective_road(curve=0.0, lateral=0.0):
    """Conceptual version of the segment projection used by the game."""
    levels = 9
    bottom_y = -3.35
    top_y = 1.35
    centers = []
    half_widths = []
    ys = []

    for index in range(levels + 1):
        percent = index / levels
        ys.append(bottom_y + (top_y - bottom_y) * percent)
        half_widths.append(5.85 * (1 - percent) ** 1.55 + 0.16)
        centers.append(-lateral * (1 - percent) + curve * percent**2)

    road = VGroup()
    for index in range(levels - 1, -1, -1):
        near_y = ys[index]
        far_y = ys[index + 1]
        near_x = centers[index]
        far_x = centers[index + 1]
        near_w = half_widths[index]
        far_w = half_widths[index + 1]
        road.add(
            Polygon(
                [near_x - near_w, near_y, 0],
                [near_x + near_w, near_y, 0],
                [far_x + far_w, far_y, 0],
                [far_x - far_w, far_y, 0],
                fill_color=ROAD_LIGHT if index % 2 else ROAD_DARK,
                fill_opacity=1,
                stroke_width=0,
            )
        )
        if index % 2:
            for lane_fraction in (-1 / 3, 1 / 3):
                road.add(
                    Polygon(
                        [near_x + near_w * lane_fraction - near_w / 50, near_y, 0],
                        [near_x + near_w * lane_fraction + near_w / 50, near_y, 0],
                        [far_x + far_w * lane_fraction + far_w / 50, far_y, 0],
                        [far_x + far_w * lane_fraction - far_w / 50, far_y, 0],
                        fill_color=WHITE,
                        fill_opacity=0.9,
                        stroke_width=0,
                    )
                )
    return road


def make_camera_background(width=6.0, height=4.7):
    panel = RoundedRectangle(
        width=width,
        height=height,
        corner_radius=0.14,
        stroke_color="#33415F",
        fill_color=PANEL,
        fill_opacity=1,
    )
    sky = Rectangle(
        width=width - 0.12,
        height=(height - 0.12) / 2,
        stroke_width=0,
        fill_color=SKY,
        fill_opacity=1,
    ).move_to(panel.get_center() + UP * (height - 0.12) / 4)
    grass = Rectangle(
        width=width - 0.12,
        height=(height - 0.12) / 2,
        stroke_width=0,
        fill_color=GRASS,
        fill_opacity=1,
    ).move_to(panel.get_center() + DOWN * (height - 0.12) / 4)
    return VGroup(panel, sky, grass)


def make_car(width):
    car = ImageMobject(str(CAR_IMAGE_PATH))
    car.width = width
    return car


class RelativePositionExplainer(Scene):
    def construct(self):
        self.camera.background_color = BACKGROUND

        # Learning goal: Understand why player_x moves the projected road while
        # the rear-view car sprite remains anchored to one screen position.
        # Narration: The game stores the driver relative to the road, but draws
        # the car at a fixed screen position.
        title = make_text("How the driver stays relative to the road", 46, TEXT, "BOLD")
        subtitle = make_text(
            "player_x changes the camera; the road projection supplies the motion",
            26,
            MUTED,
        )
        subtitle.next_to(title, DOWN, buff=0.28)

        intro_road = make_perspective_road(curve=0.65, lateral=0.0).scale(0.52)
        intro_road.shift(DOWN * 0.8)
        intro_car = make_car(2.05).move_to([0, -2.45, 0])
        fixed_line = DashedLine(
            [0, -3.35, 0], [0, -1.4, 0], color=PLAYER, dash_length=0.12
        )
        fixed_label = make_text("fixed screen x", 22, PLAYER, "BOLD")
        fixed_label.next_to(fixed_line, LEFT, buff=0.22).shift(UP * 0.3)

        self.play(Write(title), FadeIn(subtitle))
        self.play(FadeIn(intro_road), FadeIn(intro_car), Create(fixed_line), FadeIn(fixed_label))
        self.wait(1.1)
        self.play(FadeOut(Group(title, subtitle, intro_road, intro_car, fixed_line, fixed_label)))

        # Section 1
        # Narration: In road coordinates the driver moves right, while in camera
        # coordinates the road moves left under an anchored car.
        heading = make_heading("1  Two views of the same steering input", PLAYER)
        world_title = make_text("Road coordinates", 25, TEXT, "BOLD").move_to([-3.7, 2.2, 0])
        camera_title = make_text("Camera / screen coordinates", 25, TEXT, "BOLD").move_to([3.45, 2.2, 0])

        world_panel = RoundedRectangle(
            width=5.45,
            height=4.75,
            corner_radius=0.14,
            stroke_color="#33415F",
            fill_color=PANEL,
            fill_opacity=1,
        ).move_to([-3.7, -0.35, 0])
        world_road = Rectangle(
            width=2.75,
            height=4.35,
            stroke_color=WHITE,
            stroke_width=2,
            fill_color=ROAD_DARK,
            fill_opacity=1,
        ).move_to(world_panel)
        world_center = DashedLine(
            [-3.7, -2.45, 0], [-3.7, 1.75, 0], color=MUTED, dash_length=0.16
        )
        world_label = make_text("road center", 18, MUTED).rotate(1.5708)
        world_label.next_to(world_center, LEFT, buff=0.12)

        camera_panel = make_camera_background().move_to([3.45, -0.35, 0])
        player_x = ValueTracker(0.0)
        world_driver = always_redraw(
            lambda: Circle(
                radius=0.17,
                color=PLAYER,
                fill_color=PLAYER,
                fill_opacity=1,
            ).move_to([-3.7 + 1.25 * player_x.get_value(), -0.45, 0])
        )
        driver_arrow = always_redraw(
            lambda: Arrow(
                [-3.7, -1.05, 0],
                [-3.7 + 1.25 * player_x.get_value(), -1.05, 0],
                buff=0,
                color=PLAYER,
                stroke_width=5,
                max_tip_length_to_length_ratio=0.22,
            )
        )
        camera_road = always_redraw(
            lambda: make_perspective_road(
                curve=0.0,
                lateral=3.0 * player_x.get_value(),
            ).scale(0.37).shift([3.45, -0.3, 0])
        )
        camera_car = make_car(1.6).move_to([3.45, -2.05, 0])
        camera_anchor = DashedLine(
            [3.45, -2.65, 0], [3.45, -1.35, 0], color=PLAYER, dash_length=0.1
        )
        value_label = always_redraw(
            lambda: make_text(
                f"player_x = {player_x.get_value():+.2f}",
                23,
                PLAYER,
                "BOLD",
            ).move_to([0, -3.25, 0])
        )

        self.play(FadeIn(heading), FadeIn(world_title), FadeIn(camera_title))
        self.play(
            FadeIn(world_panel),
            FadeIn(world_road),
            Create(world_center),
            FadeIn(world_label),
            FadeIn(camera_panel),
            FadeIn(camera_road),
            FadeIn(world_driver),
            FadeIn(driver_arrow),
            FadeIn(camera_car),
            Create(camera_anchor),
            FadeIn(value_label),
        )
        self.play(player_x.animate.set_value(0.62), run_time=2.0)
        world_note = make_text("driver moves right", 20, PLAYER, "BOLD").move_to([-3.7, 1.42, 0])
        camera_note = make_text("road moves left", 20, BACKGROUND, "BOLD").move_to([3.45, 1.42, 0])
        self.play(FadeIn(world_note), FadeIn(camera_note))
        self.wait(1.1)
        section_one = Group(
            heading,
            world_title,
            camera_title,
            world_panel,
            world_road,
            world_center,
            world_label,
            camera_panel,
            world_note,
            camera_note,
            camera_car,
            camera_anchor,
        )
        self.play(
            FadeOut(section_one),
            FadeOut(world_driver),
            FadeOut(driver_arrow),
            FadeOut(camera_road),
            FadeOut(value_label),
        )

        # Section 2
        # Narration: The steering keys update player_x; they never change the
        # screen rectangle used to draw the car sprite.
        heading2 = make_heading("2  Steering updates only player_x", UPDATE)
        update_code = make_code_panel(
            [
                "steering = right - left",
                "player_x = move_player(",
                "    player_x, steering, FIXED_STEP)",
                "return player_x + steering *",
                "    PLAYER_LATERAL_SPEED * dt",
            ],
            width=6.4,
            font_size=19,
        ).move_to([-3.35, -0.1, 0])
        update_highlight = line_highlight(update_code, 1, UPDATE)

        meter_line = Line([1.0, -0.25, 0], [6.0, -0.25, 0], color=MUTED, stroke_width=4)
        meter_center = Line([3.5, -0.45, 0], [3.5, -0.05, 0], color=WHITE, stroke_width=3)
        left_label = make_text("left", 20, MUTED).next_to(meter_line, DOWN).align_to(meter_line, LEFT)
        right_label = make_text("right", 20, MUTED).next_to(meter_line, DOWN).align_to(meter_line, RIGHT)
        variable_dot = Circle(
            radius=0.16,
            color=PLAYER,
            fill_color=PLAYER,
            fill_opacity=1,
        ).move_to(meter_line.get_center())
        variable_label = make_text("player_x = 0.00", 26, PLAYER, "BOLD").move_to([3.5, 0.75, 0])
        fixed_code = make_code_panel(
            [
                "car_rect = car_image.get_rect(",
                "    midbottom=(SCREEN_WIDTH // 2, ...))",
            ],
            width=5.9,
            font_size=17,
        ).move_to([3.5, -1.65, 0])
        fixed_note = make_text("car_rect is created once", 22, DRAW, "BOLD")
        fixed_note.next_to(fixed_code, DOWN, buff=0.25)

        self.play(FadeIn(heading2), FadeIn(update_code), Create(update_highlight))
        self.play(
            Create(meter_line),
            Create(meter_center),
            FadeIn(left_label),
            FadeIn(right_label),
            FadeIn(variable_dot),
            FadeIn(variable_label),
        )
        right_value = make_text("player_x = +0.35", 26, PLAYER, "BOLD").move_to(variable_label)
        self.play(
            variable_dot.animate.move_to([4.375, -0.25, 0]),
            Transform(variable_label, right_value),
            run_time=1.2,
        )
        self.play(FadeIn(fixed_code), FadeIn(fixed_note))
        self.play(Indicate(fixed_note, color=DRAW))
        self.wait(0.8)
        self.play(
            FadeOut(
                Group(
                    heading2,
                    update_code,
                    update_highlight,
                    meter_line,
                    meter_center,
                    left_label,
                    right_label,
                    variable_dot,
                    variable_label,
                    fixed_code,
                    fixed_note,
                )
            )
        )

        # Section 3
        # Narration: Projection turns the player's road-relative position into a
        # camera offset, and the minus sign moves road pixels the opposite way.
        heading3 = make_heading("3  Projection converts player_x into pixels", PROJECT)
        project_code = make_code_panel(
            [
                "camera_x = player_x * ROAD_WIDTH",
                "           - curve_offset",
                "screen_x = SCREEN_WIDTH / 2",
                "           - scale * camera_x",
                "             * SCREEN_WIDTH / 2",
            ],
            width=6.6,
            font_size=18,
        ).move_to([-3.35, -0.15, 0])
        camera_highlight = line_highlight(project_code, 0, PLAYER)

        inputs = VGroup(
            make_text("player_x = +0.50", 24, PLAYER, "BOLD"),
            make_text("ROAD_WIDTH = 2000", 24, MUTED),
            make_text("curve_offset = 0", 24, CURVE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to([3.4, 1.05, 0])
        result = make_text("camera_x = +1000", 28, PLAYER, "BOLD").move_to([3.4, -0.25, 0])
        result_box = SurroundingRectangle(result, buff=0.18, color=PLAYER, stroke_width=2)

        screen_axis = Line([1.0, -1.65, 0], [6.0, -1.65, 0], color=MUTED, stroke_width=4)
        screen_center = Line([3.5, -1.9, 0], [3.5, -1.4, 0], color=WHITE, stroke_width=3)
        center_label = make_text("screen center", 18, MUTED).next_to(screen_center, DOWN, buff=0.13)
        road_pixel = Circle(
            radius=0.16,
            color=PROJECT,
            fill_color=PROJECT,
            fill_opacity=1,
        ).move_to([3.5, -1.65, 0])
        left_arrow = Arrow(
            [3.5, -1.15, 0],
            [2.25, -1.15, 0],
            buff=0,
            color=PROJECT,
            stroke_width=5,
        )
        opposite_note = make_text("positive camera_x -> road pixel shifts left", 20, PROJECT, "BOLD")
        opposite_note.move_to([3.5, -2.75, 0])

        self.play(FadeIn(heading3), FadeIn(project_code), Create(camera_highlight))
        self.play(FadeIn(inputs, shift=UP * 0.2))
        self.play(FadeIn(result), Create(result_box))
        screen_highlight = line_highlight(project_code, 2, PROJECT)
        self.play(ReplacementTransform(camera_highlight, screen_highlight))
        self.play(Create(screen_axis), Create(screen_center), FadeIn(center_label), FadeIn(road_pixel))
        self.play(GrowArrow(left_arrow), road_pixel.animate.move_to([2.25, -1.65, 0]))
        self.play(FadeIn(opposite_note))
        self.wait(1.0)
        self.play(
            FadeOut(
                VGroup(
                    heading3,
                    project_code,
                    screen_highlight,
                    inputs,
                    result,
                    result_box,
                    screen_axis,
                    screen_center,
                    center_label,
                    road_pixel,
                    left_arrow,
                    opposite_note,
                )
            )
        )

        # Section 4
        # Narration: Every road segment shares the same player offset, but each
        # segment accumulates a different curve offset.
        heading4 = make_heading("4  Curves add a different offset per segment", CURVE)
        curve_code = make_code_panel(
            [
                "camera_x = player_x * ROAD_WIDTH",
                "           - curve_offset",
                "curve_offset += curve_velocity",
                "curve_velocity += track[segment_index]",
            ],
            width=6.7,
            font_size=18,
        ).move_to([-3.35, -0.1, 0])
        curve_highlight = line_highlight(curve_code, 2, CURVE)
        same_term = make_text("same player_x term", 23, PLAYER, "BOLD").move_to([3.55, 2.0, 0])

        straight_segments = VGroup()
        curved_segments = VGroup()
        offsets = [0.0, 0.12, 0.32, 0.60, 0.95, 1.35]
        for index, offset in enumerate(offsets):
            y = -2.15 + index * 0.65
            width = 4.9 - index * 0.55
            straight_segments.add(Line([3.5 - width / 2, y, 0], [3.5 + width / 2, y, 0], color=ROAD_LIGHT, stroke_width=18))
            curved_segments.add(Line([3.5 - width / 2 + offset, y, 0], [3.5 + width / 2 + offset, y, 0], color=ROAD_LIGHT, stroke_width=18))

        straight_center = DashedLine([3.5, -2.55, 0], [3.5, 1.45, 0], color=MUTED, dash_length=0.13)
        curve_arrow = Arrow([3.5, -2.75, 0], [4.85, -2.75, 0], color=CURVE, stroke_width=5)
        curve_note = make_text("different curve_offset", 22, CURVE, "BOLD").next_to(curve_arrow, DOWN, buff=0.13)

        self.play(FadeIn(heading4), FadeIn(curve_code), Create(curve_highlight))
        self.play(FadeIn(same_term), Create(straight_center), FadeIn(straight_segments))
        self.play(Transform(straight_segments, curved_segments), GrowArrow(curve_arrow), FadeIn(curve_note), run_time=2.0)
        self.wait(1.0)
        self.play(
            FadeOut(
                VGroup(
                    heading4,
                    curve_code,
                    curve_highlight,
                    same_term,
                    straight_segments,
                    straight_center,
                    curve_arrow,
                    curve_note,
                )
            )
        )

        # Section 5
        # Narration: The renderer draws the shifted road first and then draws the
        # car with the same car_rect, completing the illusion of driving.
        heading5 = make_heading("5  The renderer combines both coordinate systems", BACKGROUND)
        sky = Rectangle(width=14.25, height=3.5, stroke_width=0, fill_color=SKY, fill_opacity=1).move_to([0, 1.65, 0])
        grass = Rectangle(width=14.25, height=3.8, stroke_width=0, fill_color=GRASS, fill_opacity=1).move_to([0, -1.95, 0])
        final_road = make_perspective_road(curve=0.0, lateral=0.0)
        final_car = make_car(2.2).move_to([0, -2.7, 0])
        final_anchor = DashedLine([0, -3.7, 0], [0, -1.85, 0], color=PLAYER, dash_length=0.12)
        anchor_label = make_text("unchanged car_rect", 21, PLAYER, "BOLD").move_to([-2.1, -2.05, 0])
        render_code = make_code_panel(
            [
                "draw_road(screen, track, position, player_x)",
                "screen.blit(car_image, car_rect)",
            ],
            width=6.6,
            font_size=17,
        ).move_to([-3.35, 1.8, 0])
        render_highlight = line_highlight(render_code, 0, DRAW)
        motion_note = make_text("player_x increases -> projected road moves left", 22, BACKGROUND, "BOLD")
        motion_note.move_to([3.55, 2.2, 0])

        self.play(FadeIn(sky), FadeIn(grass), FadeIn(final_road), FadeIn(heading5))
        self.play(FadeIn(final_car), Create(final_anchor), FadeIn(anchor_label))
        self.play(FadeIn(render_code), Create(render_highlight), FadeIn(motion_note))
        shifted_road = make_perspective_road(curve=0.9, lateral=1.55)
        self.play(Transform(final_road, shifted_road), run_time=2.2)
        car_highlight = line_highlight(render_code, 1, PLAYER)
        self.play(ReplacementTransform(render_highlight, car_highlight), Indicate(final_car, color=PLAYER))
        self.wait(1.0)
        self.play(
            FadeOut(
                Group(
                    sky,
                    grass,
                    final_road,
                    final_car,
                    final_anchor,
                    anchor_label,
                    render_code,
                    car_highlight,
                    motion_note,
                    heading5,
                )
            )
        )

        # Recap
        # Narration: The player lives in road coordinates, projection moves the
        # road in screen coordinates, and the sprite remains the visual anchor.
        recap_title = make_text("Relative position creates the driving illusion", 42, TEXT, "BOLD")
        recap_title.to_edge(UP, buff=0.65)
        recap = VGroup(
            make_text("1   steering changes player_x", 28, UPDATE),
            make_text("2   player_x becomes camera_x", 28, PLAYER),
            make_text("3   camera_x shifts projected road pixels", 28, PROJECT),
            make_text("4   curve_offset bends individual segments", 28, CURVE),
            make_text("5   car_rect stays fixed on screen", 28, DRAW),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.38).move_to([0, -0.25, 0])
        final_formula = make_text(
            "driver moves in road space  ->  road moves in screen space",
            27,
            TEXT,
            "BOLD",
        ).to_edge(DOWN, buff=0.65)

        self.play(Write(recap_title))
        self.play(FadeIn(recap, shift=UP * 0.2))
        self.play(FadeIn(final_formula))
        self.wait(2.0)
