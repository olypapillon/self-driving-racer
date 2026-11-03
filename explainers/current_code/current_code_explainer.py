from pathlib import Path

from manim import (
    BLACK,
    DOWN,
    FadeIn,
    FadeOut,
    GrowArrow,
    ImageMobject,
    LEFT,
    Line,
    ORIGIN,
    Polygon,
    Rectangle,
    ReplacementTransform,
    RIGHT,
    RoundedRectangle,
    Scene,
    SurroundingRectangle,
    Text,
    Transform,
    TransformFromCopy,
    UP,
    VGroup,
    WHITE,
    Write,
    Arrow,
    Circle,
    Create,
    Ellipse,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CAR_IMAGE_PATH = PROJECT_ROOT / "assets" / "car-rear.png"

BACKGROUND = "#0B1020"
PANEL = "#151D32"
TEXT = "#ECF2FF"
MUTED = "#9FB0CF"
TRACK = "#58A6FF"
UPDATE = "#F2CC60"
PROJECT = "#C297FF"
DRAW = "#63D297"
CURVE_RIGHT = "#FF8A65"
CURVE_LEFT = "#54D1DB"
ROAD_LIGHT = "#565B66"
ROAD_DARK = "#444954"
GRASS = "#176B3A"


def make_text(content, size=28, color=TEXT, weight="NORMAL"):
    return Text(content, font_size=size, color=color, weight=weight)


def make_section_heading(content, color):
    heading = make_text(content, 34, color, "BOLD")
    heading.to_corner(UP + LEFT, buff=0.45).shift(DOWN * 0.62)
    return heading


def make_code_panel(lines, width=6.25):
    code_lines = VGroup(
        *[
            Text(line, font="Monospace", font_size=20, color=TEXT)
            for line in lines
        ]
    ).arrange(DOWN, aligned_edge=LEFT, buff=0.13)
    panel = RoundedRectangle(
        width=width,
        height=code_lines.height + 0.48,
        corner_radius=0.14,
        stroke_color="#33415F",
        stroke_width=1.5,
        fill_color=PANEL,
        fill_opacity=1,
    )
    code_lines.move_to(panel).align_to(panel, LEFT).shift(RIGHT * 0.25)
    return VGroup(panel, code_lines)


def line_highlight(panel, index, color=UPDATE):
    line = panel[1][index]
    return SurroundingRectangle(
        line,
        buff=0.06,
        color=color,
        stroke_width=2,
        fill_color=color,
        fill_opacity=0.12,
    )


def make_pipeline():
    names = [("track", TRACK), ("update", UPDATE), ("project", PROJECT), ("draw", DRAW)]
    boxes = VGroup()
    arrows = VGroup()
    for name, color in names:
        box = RoundedRectangle(
            width=2.25,
            height=0.72,
            corner_radius=0.13,
            stroke_color=color,
            fill_color=color,
            fill_opacity=0.12,
        )
        label = make_text(name, 25, color, "BOLD").move_to(box)
        boxes.add(VGroup(box, label))
    boxes.arrange(RIGHT, buff=0.72)
    for left_box, right_box in zip(boxes[:-1], boxes[1:]):
        arrows.add(
            Arrow(
                left_box.get_right(),
                right_box.get_left(),
                buff=0.09,
                color=MUTED,
                stroke_width=3,
                max_tip_length_to_length_ratio=0.16,
            )
        )
    return VGroup(boxes, arrows)


def pipeline_focus(pipeline, index):
    return SurroundingRectangle(
        pipeline[0][index],
        buff=0.08,
        color=WHITE,
        stroke_width=3,
    )


def make_perspective_road(curve=1.0, lateral=0.0):
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


class CurrentCodeExplainer(Scene):
    def construct(self):
        self.camera.background_color = BACKGROUND

        # Learning goal: Understand how track data becomes one pseudo-3D frame.
        # Narration: The program repeats four jobs to turn a list of curves into a driving view.
        title = make_text("How the current pseudo-3D racer works", 44, TEXT, "BOLD")
        title.to_edge(UP, buff=0.55)
        goal = make_text(
            "Learning goal: follow one frame from track data to pixels",
            27,
            MUTED,
        ).next_to(title, DOWN, buff=0.25)
        pipeline = make_pipeline().scale(0.9).move_to(ORIGIN + DOWN * 0.25)
        self.play(Write(title), FadeIn(goal, shift=UP * 0.15))
        self.play(FadeIn(pipeline[0], shift=UP * 0.2))
        self.play(*[GrowArrow(arrow) for arrow in pipeline[1]])
        self.wait(1)
        self.play(
            FadeOut(title),
            FadeOut(goal),
            pipeline.animate.scale(0.56).to_edge(UP, buff=0.28),
        )

        # Section 1 — input data.
        # Narration: build_track stores one curve number for every 200-unit road segment.
        section = make_section_heading("1  Track data", TRACK)
        focus = pipeline_focus(pipeline, 0)
        track_code = make_code_panel(
            [
                "track = []",
                "add_straight(track, 60)",
                "add_road(..., curve= 2.0)",
                "add_road(..., curve=-2.0)",
                "return track",
            ]
        ).scale(0.88).to_edge(LEFT, buff=0.45).shift(DOWN * 0.35)

        segment_colors = [TRACK] * 4 + [CURVE_RIGHT] * 5 + [CURVE_LEFT] * 5 + [TRACK] * 4
        segments = VGroup(
            *[
                Rectangle(
                    width=0.38,
                    height=1.0,
                    stroke_color=color,
                    fill_color=color,
                    fill_opacity=0.55,
                )
                for color in segment_colors
            ]
        ).arrange(RIGHT, buff=0.05).scale(0.92)
        segments.to_edge(RIGHT, buff=0.45).shift(UP * 0.05)
        labels = VGroup(
            make_text("0.0 straight", 21, TRACK),
            make_text("+2.0 right", 21, CURVE_RIGHT),
            make_text("-2.0 left", 21, CURVE_LEFT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.16)
        labels.next_to(segments, DOWN, buff=0.45)
        chosen = SurroundingRectangle(segments[6], buff=0.05, color=WHITE, stroke_width=3)
        chosen_label = make_text("one segment", 21, WHITE).next_to(chosen, UP, buff=0.12)

        self.play(Write(section), Create(focus), FadeIn(track_code))
        self.play(FadeIn(segments, lag_ratio=0.05), FadeIn(labels))
        self.play(Create(chosen), FadeIn(chosen_label))
        self.wait(1)

        # Section 2 — variables changed by the fixed update.
        # Narration: Every fixed step moves the camera forward and optionally changes player_x.
        next_section = make_section_heading("2  Fixed-step update", UPDATE)
        next_focus = pipeline_focus(pipeline, 1)
        update_code = make_code_panel(
            [
                "while accumulator >= 1/60:",
                "  position += 2400 * 1/60",
                "  player_x += steering * 0.7 * 1/60",
                "  accumulator -= 1/60",
            ]
        ).scale(0.9).to_edge(LEFT, buff=0.45).shift(DOWN * 0.25)
        clock = Circle(radius=0.78, color=UPDATE, stroke_width=4).shift(RIGHT * 3.6 + UP * 0.65)
        hand = Line(clock.get_center(), clock.get_center() + UP * 0.58, color=UPDATE, stroke_width=4)
        fixed_label = make_text("FIXED_STEP = 1/60 s", 24, UPDATE).next_to(clock, DOWN, buff=0.22)
        values_before = VGroup(
            make_text("position:  0", 27),
            make_text("player_x:  0", 27),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).next_to(fixed_label, DOWN, buff=0.45)
        values_after = VGroup(
            make_text("position:  40", 27, DRAW),
            make_text("player_x:  0.0117  (D held)", 27, DRAW),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(values_before, aligned_edge=LEFT)

        self.play(
            ReplacementTransform(section, next_section),
            ReplacementTransform(focus, next_focus),
            FadeOut(track_code),
            FadeOut(segments),
            FadeOut(labels),
            FadeOut(chosen),
            FadeOut(chosen_label),
            FadeIn(update_code),
        )
        update_highlight = line_highlight(update_code, 0, UPDATE)
        self.play(Create(clock), Create(hand), FadeIn(fixed_label), Create(update_highlight))
        self.play(FadeIn(values_before))
        self.play(
            Transform(update_highlight, line_highlight(update_code, 1, UPDATE)),
            hand.animate.rotate(-6.283 / 6, about_point=clock.get_center()),
            ReplacementTransform(values_before, values_after),
        )
        self.play(Transform(update_highlight, line_highlight(update_code, 2, UPDATE)))
        self.wait(1)

        # Section 3 — one point through the projection formula.
        # Narration: Dividing by camera-space Z makes near geometry large and far geometry small.
        projection_section = make_section_heading("3  Project one point", PROJECT)
        projection_focus = pipeline_focus(pipeline, 2)
        projection_code = make_code_panel(
            [
                "camera_space_z = world_z - camera_z",
                "scale = CAMERA_DEPTH / camera_space_z",
                "screen_x = center - scale * camera_x",
                "screen_y = center + scale * CAMERA_HEIGHT",
                "screen_width = scale * ROAD_WIDTH",
            ]
        ).scale(0.78).to_edge(LEFT, buff=0.38).shift(DOWN * 0.3)
        axis = Line([0.8, -0.6, 0], [6.1, -0.6, 0], color=MUTED, stroke_width=3)
        camera = Polygon(
            [0.55, -0.9, 0], [0.55, -0.3, 0], [1.08, -0.6, 0],
            color=UPDATE, fill_color=UPDATE, fill_opacity=0.65,
        )
        near_dot = Circle(radius=0.11, color=CURVE_RIGHT, fill_opacity=1).move_to([2.5, -0.6, 0])
        far_dot = Circle(radius=0.11, color=CURVE_LEFT, fill_opacity=1).move_to([5.65, -0.6, 0])
        near_label = make_text("z = 1000", 21, CURVE_RIGHT).next_to(near_dot, UP, buff=0.15)
        far_label = make_text("z = 3000", 21, CURVE_LEFT).next_to(far_dot, UP, buff=0.15)
        near_bar = Rectangle(width=2.35, height=0.28, color=CURVE_RIGHT, fill_opacity=0.7).move_to([3.0, 1.35, 0])
        far_bar = Rectangle(width=0.78, height=0.18, color=CURVE_LEFT, fill_opacity=0.7).move_to([3.0, 2.25, 0])
        formula = make_text("scale = CAMERA_DEPTH / camera_space_z", 24, PROJECT)
        formula.next_to(axis, DOWN, buff=0.52)

        self.play(
            ReplacementTransform(next_section, projection_section),
            ReplacementTransform(next_focus, projection_focus),
            FadeOut(update_code),
            FadeOut(update_highlight),
            FadeOut(clock),
            FadeOut(hand),
            FadeOut(fixed_label),
            FadeOut(values_after),
            FadeIn(projection_code),
        )
        projection_highlight = line_highlight(projection_code, 0, PROJECT)
        self.play(Create(axis), FadeIn(camera), FadeIn(near_dot), FadeIn(far_dot), FadeIn(near_label), FadeIn(far_label))
        self.play(Create(projection_highlight), FadeIn(formula))
        self.play(Transform(projection_highlight, line_highlight(projection_code, 1, PROJECT)))
        self.play(TransformFromCopy(near_dot, near_bar), TransformFromCopy(far_dot, far_bar))
        size_note = make_text("near = wide and low    •    far = narrow and high", 22, MUTED)
        size_note.next_to(formula, DOWN, buff=0.24)
        self.play(FadeIn(size_note))
        self.wait(1)

        # Section 4 — repeat for visible segments.
        # Narration: projected_road repeats that projection and rejects points behind the camera.
        repeat_section = make_section_heading("4  Project visible segments", PROJECT)
        repeat_code = make_code_panel(
            [
                "for distance in range(DRAW_DISTANCE):",
                "  near = project_point(...) ",
                "  far  = project_point(...) ",
                "  if near is None: continue",
                "  visible.append((near, far, index))",
            ]
        ).scale(0.83).to_edge(LEFT, buff=0.42).shift(DOWN * 0.25)
        trapezoids = VGroup()
        for index in range(7):
            near_y = -2.8 + index * 0.52
            far_y = near_y + 0.52
            near_w = 3.2 * (1 - index / 8) + 0.4
            far_w = 3.2 * (1 - (index + 1) / 8) + 0.4
            center_near = 3.55 + 0.035 * index**2
            center_far = 3.55 + 0.035 * (index + 1) ** 2
            trapezoids.add(
                Polygon(
                    [center_near - near_w, near_y, 0],
                    [center_near + near_w, near_y, 0],
                    [center_far + far_w, far_y, 0],
                    [center_far - far_w, far_y, 0],
                    fill_color=ROAD_LIGHT if index % 2 else ROAD_DARK,
                    fill_opacity=1,
                    stroke_color="#757D8F",
                    stroke_width=1,
                )
            )

        self.play(
            ReplacementTransform(projection_section, repeat_section),
            FadeOut(projection_code),
            FadeOut(projection_highlight),
            FadeOut(axis),
            FadeOut(camera),
            FadeOut(near_dot),
            FadeOut(far_dot),
            FadeOut(near_label),
            FadeOut(far_label),
            FadeOut(near_bar),
            FadeOut(far_bar),
            FadeOut(formula),
            FadeOut(size_note),
            FadeIn(repeat_code),
        )
        repeat_highlight = line_highlight(repeat_code, 0, PROJECT)
        self.play(Create(repeat_highlight))
        for trapezoid in reversed(trapezoids):
            self.play(FadeIn(trapezoid), run_time=0.18)
        self.play(Transform(repeat_highlight, line_highlight(repeat_code, 4, PROJECT)))
        visible_label = make_text("visible[]", 24, PROJECT, "BOLD").next_to(trapezoids, UP, buff=0.2)
        self.play(FadeIn(visible_label))
        self.wait(0.8)

        # Section 5 — curve accumulation.
        # Narration: curve_velocity changes the offset faster on every curved segment.
        curve_section = make_section_heading("5  Fake curves with x and dx", CURVE_RIGHT)
        curve_code = make_code_panel(
            [
                "curve_offset += curve_velocity",
                "curve_velocity += track[segment_index]",
                "camera_x = player_x * ROAD_WIDTH",
                "camera_x -= curve_offset",
            ]
        ).scale(0.9).to_edge(LEFT, buff=0.42).shift(DOWN * 0.25)
        curve_points = VGroup()
        curve_arrows = VGroup()
        curve_values = [(0.0, 0.0), (0.0, 2.0), (2.0, 4.0), (6.0, 6.0), (12.0, 8.0)]
        for index, (offset, velocity) in enumerate(curve_values):
            point = Circle(radius=0.1, color=CURVE_RIGHT, fill_opacity=1)
            point.move_to([2.0 + offset * 0.18, -2.45 + index * 0.95, 0])
            value = make_text(f"x={offset:g}   dx={velocity:g}", 20, MUTED).next_to(point, RIGHT, buff=0.2)
            curve_points.add(VGroup(point, value))
        for first, second in zip(curve_points[:-1], curve_points[1:]):
            curve_arrows.add(
                Arrow(
                    first[0].get_center(),
                    second[0].get_center(),
                    buff=0.13,
                    color=CURVE_RIGHT,
                    stroke_width=3,
                    max_tip_length_to_length_ratio=0.18,
                )
            )

        self.play(
            ReplacementTransform(repeat_section, curve_section),
            FadeOut(repeat_code),
            FadeOut(repeat_highlight),
            FadeOut(trapezoids),
            FadeOut(visible_label),
            FadeIn(curve_code),
        )
        curve_highlight = line_highlight(curve_code, 0, CURVE_RIGHT)
        self.play(Create(curve_highlight), FadeIn(curve_points[0]))
        for index in range(1, len(curve_points)):
            self.play(GrowArrow(curve_arrows[index - 1]), FadeIn(curve_points[index]), run_time=0.45)
            self.play(
                Transform(
                    curve_highlight,
                    line_highlight(curve_code, index % 2, CURVE_RIGHT),
                ),
                run_time=0.25,
            )
        curve_note = make_text("constant curve  →  increasing sideways bend", 23, CURVE_RIGHT)
        curve_note.to_edge(RIGHT, buff=0.55).shift(DOWN * 2.9)
        self.play(FadeIn(curve_note))
        self.wait(1)

        # Section 6 — complete frame.
        # Narration: The road is drawn far-to-near, then the fixed shadow and car are placed on top.
        final_section = make_section_heading("6  Draw the complete frame", BACKGROUND)
        draw_focus = pipeline_focus(pipeline, 3)
        final_code = make_code_panel(
            [
                "for segment in reversed(visible):",
                "  draw_segment(screen, near, far, index)",
                "screen.blit(car_shadow, shadow_rect)",
                "screen.blit(car_image, car_rect)",
            ],
            width=6.7,
        ).scale(0.73).to_edge(LEFT, buff=0.28).shift(UP * 0.65)
        final_road = make_perspective_road(curve=1.05, lateral=0.0)
        final_road.set_z_index(-2)
        grass = Rectangle(
            width=14.4,
            height=4.9,
            fill_color=GRASS,
            fill_opacity=1,
            stroke_width=0,
        ).move_to(DOWN * 1.05).set_z_index(-3)
        sky = Rectangle(
            width=14.4,
            height=3.25,
            fill_color="#65BCE6",
            fill_opacity=1,
            stroke_width=0,
        ).move_to(UP * 2.15).set_z_index(-3)
        car = ImageMobject(str(CAR_IMAGE_PATH)).scale_to_fit_width(3.4)
        car.move_to([0, -2.75, 0]).set_z_index(3)
        shadow = Ellipse(
            width=3.35,
            height=0.42,
            fill_color=BLACK,
            fill_opacity=0.42,
            stroke_width=0,
        ).move_to([0, -3.02, 0]).set_z_index(1)
        anchored = make_text("car stays anchored", 23, WHITE, "BOLD").next_to(car, UP, buff=0.12)
        player_note = make_text(
            "A/D changes player_x; the road shifts",
            22,
            BACKGROUND,
            "BOLD",
        ).move_to([3.35, 2.55, 0])

        self.play(
            ReplacementTransform(curve_section, final_section),
            ReplacementTransform(projection_focus, draw_focus),
            FadeOut(curve_code),
            FadeOut(curve_highlight),
            FadeOut(curve_points),
            FadeOut(curve_arrows),
            FadeOut(curve_note),
            FadeIn(sky),
            FadeIn(grass),
            FadeIn(final_code),
        )
        final_highlight = line_highlight(final_code, 0, DRAW)
        self.play(Create(final_highlight), FadeIn(final_road))
        self.play(
            Transform(final_highlight, line_highlight(final_code, 2, DRAW)),
            FadeIn(shadow),
        )
        self.play(
            Transform(final_highlight, line_highlight(final_code, 3, DRAW)),
            FadeIn(car, shift=UP * 0.15),
            FadeIn(anchored),
        )
        shifted_road = make_perspective_road(curve=1.05, lateral=0.45).set_z_index(-2)
        self.play(
            Transform(final_road, shifted_road),
            FadeIn(player_note),
            run_time=1.3,
        )
        self.wait(1)

        # Recap.
        # Narration: Position drives forward motion, player_x drives lateral motion, and projection creates depth.
        recap_title = make_text("One frame, four responsibilities", 40, TEXT, "BOLD").to_edge(UP, buff=0.6)
        recap = VGroup(
            make_text("position  →  forward progress", 27, UPDATE),
            make_text("player_x  →  road-relative steering", 27, TRACK),
            make_text("camera_depth / z  →  perspective", 27, PROJECT),
            make_text("x + dx  →  curves", 27, CURVE_RIGHT),
            make_text("far-to-near draw  →  final frame", 27, DRAW),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28).move_to(ORIGIN + DOWN * 0.2)
        self.play(
            FadeOut(pipeline),
            FadeOut(final_section),
            FadeOut(draw_focus),
            FadeOut(final_code),
            FadeOut(final_highlight),
            FadeOut(sky),
            FadeOut(grass),
            FadeOut(final_road),
            FadeOut(shadow),
            FadeOut(car),
            FadeOut(anchored),
            FadeOut(player_note),
            FadeIn(recap_title),
        )
        self.play(FadeIn(recap, lag_ratio=0.18))
        self.wait(2)
