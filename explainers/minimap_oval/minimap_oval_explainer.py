import importlib.util
import math
from pathlib import Path

import numpy as np
from manim import (
    Arrow,
    Create,
    DashedLine,
    Dot,
    DOWN,
    FadeIn,
    FadeOut,
    LEFT,
    Line,
    PI,
    RIGHT,
    RoundedRectangle,
    Scene,
    SurroundingRectangle,
    Text,
    Transform,
    UP,
    ValueTracker,
    VGroup,
    VMobject,
    Write,
    always_redraw,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
GAME_PATH = PROJECT_ROOT / "src" / "3D-game.py"

BACKGROUND = "#0B1020"
PANEL = "#151D32"
TEXT = "#ECF2FF"
MUTED = "#9FB0CF"
SEGMENT = "#58A6FF"
CURVE = "#FF8A65"
HEADING = "#C297FF"
PATH = "#63D297"
EASING = "#F2CC60"
WARNING = "#FF6B6B"
PLAYER = "#E5383B"
CODE_FONT = "Menlo"


def load_game():
    """Import src/3D-game.py so the video uses the real track numbers."""
    spec = importlib.util.spec_from_file_location("racer", GAME_PATH)
    game = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(game)
    return game


GAME = load_game()
TRACK = GAME.build_track()
TRACK_POINTS = GAME.track_path(TRACK)
HALF = len(TRACK) // 2


def old_track():
    """The track before the oval redesign, rebuilt from its old recipe."""
    curve_easy, curve_medium, hill_medium = 2.0, 4.0, 40
    hill_low = GAME.HILL_LOW
    add_road, add_straight, add_hill = GAME.add_road, GAME.add_straight, GAME.add_hill
    track = []
    add_straight(track, 60)
    add_hill(track, 50, hill_low)
    add_hill(track, 50, -hill_low)
    add_road(track, 40, 60, 40, curve_easy, hill_low)
    add_road(track, 40, 60, 40, -curve_easy, -hill_low)
    for curve, hill in (
        (0.0, hill_low / 2),
        (0.0, -hill_low),
        (curve_easy, hill_low),
        (0.0, 0.0),
        (-curve_easy, hill_low / 2),
        (0.0, 0.0),
    ):
        add_road(track, 45, 45, 45, curve, hill)
    add_straight(track, 50)
    add_hill(track, 90, hill_medium)
    add_hill(track, 90, -hill_medium)
    add_road(track, 60, 120, 60, -curve_medium, hill_low)
    add_road(track, 40, 60, 40, curve_easy, -hill_low)
    add_road(
        track, 100, 100, 100, -curve_easy, -GAME.last_elevation(track) / 200
    )
    return track


def walk(track, degrees_per_curve):
    """Same walk as track_path, with a chosen turning scale."""
    heading = math.pi / 2
    x = y = 0.0
    points = [(x, y)]
    for curve, _ in track:
        heading += math.radians(curve * degrees_per_curve)
        x += math.sin(heading)
        y -= math.cos(heading)
        points.append((x, y))
    return points


def fit(points, width, height, center):
    """Scale track points into a box; flip y because screen y points down."""
    xs = [x for x, _ in points]
    ys = [-y for _, y in points]
    scale = min(width / (max(xs) - min(xs)), height / (max(ys) - min(ys)))
    mid_x = (max(xs) + min(xs)) / 2
    mid_y = (max(ys) + min(ys)) / 2
    return [
        np.array([center[0] + (x - mid_x) * scale, center[1] + (y - mid_y) * scale, 0])
        for x, y in zip(xs, ys)
    ]


def polyline(points, color, width=5):
    line = VMobject(stroke_color=color, stroke_width=width)
    line.set_points_as_corners(points)
    return line


def make_text(content, size=28, color=TEXT, weight="NORMAL"):
    return Text(content, font_size=size, color=color, weight=weight)


def make_code(content, size=24, color=TEXT):
    return Text(content, font_size=size, color=color, font=CODE_FONT)


def make_heading(content, color=TEXT):
    heading = make_text(content, 35, color, "BOLD")
    heading.to_corner(UP + LEFT, buff=0.45).shift(DOWN * 0.58)
    return heading


def make_panel(width, height, center):
    return RoundedRectangle(
        width=width,
        height=height,
        corner_radius=0.14,
        stroke_color="#33415F",
        stroke_width=1.5,
        fill_color=PANEL,
        fill_opacity=1,
    ).move_to(center)


def code_block(lines, center, size=24):
    block = VGroup(*[make_code(line, size) for line in lines])
    block.arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(center)
    return block


class MinimapOvalExplainer(Scene):
    def construct(self):
        self.camera.background_color = BACKGROUND
        self.intro()
        self.curves_have_no_position()
        self.walk_the_track()
        self.two_rules_for_a_loop()
        self.two_identical_halves()
        self.add_corner_math()
        self.cache_and_player_dot()
        self.recap()

    def clear_scene(self):
        self.play(FadeOut(*self.mobjects))

    def intro(self):
        # Learning goal: understand how the game turns per-segment curve
        # numbers into a closed oval mini map with a smoothly moving dot.
        # Narration: The road you drive is a list of numbers. Let's turn it
        # into a map.
        title = make_text("From curve numbers to a mini map", 48, TEXT, "BOLD")
        subtitle = make_text(
            "How src/3D-game.py draws the oval in the corner", 27, MUTED
        ).next_to(title, DOWN, buff=0.28)
        oval = polyline(fit(TRACK_POINTS, 5.0, 1.6, [0, -1.9]), PATH, 6)
        self.play(Write(title), FadeIn(subtitle))
        self.play(Create(oval), run_time=2.2)
        self.wait(0.6)
        self.clear_scene()

    def curves_have_no_position(self):
        # Narration: Each segment stores only how much it bends and its
        # height. Nothing says where it is on a map.
        heading = make_heading("1  A segment knows how much it bends, not where it is", SEGMENT)
        samples = [0, 300, 600, 640, 700, 900, 1100, 1140]
        cells = VGroup()
        for index in samples:
            curve, elevation = TRACK[index]
            box = RoundedRectangle(
                width=1.45,
                height=1.45,
                corner_radius=0.12,
                stroke_color=SEGMENT,
                fill_color=SEGMENT,
                fill_opacity=0.12,
            )
            label = make_code(f"[{index}]", 18, MUTED).next_to(box, UP, buff=0.12)
            value = make_code(f"{curve:.2f}", 24, CURVE).move_to(box)
            cells.add(VGroup(box, label, value))
        cells.arrange(RIGHT, buff=0.18).move_to([0, 0.5, 0])
        caption = make_code("track[i] = (curve, elevation)", 26, TEXT).next_to(
            cells, DOWN, buff=0.7
        )
        note = make_text(
            "straights: curve 0    bend: curve eases up to ~1.9", 24, MUTED
        ).next_to(caption, DOWN, buff=0.35)
        question = make_text("No x. No y. So where do we draw it?", 28, WARNING, "BOLD")
        question.to_edge(DOWN, buff=0.5)

        self.play(Write(heading))
        self.play(FadeIn(cells, lag_ratio=0.12), run_time=1.8)
        self.play(FadeIn(caption), FadeIn(note))
        self.wait(0.6)
        self.play(FadeIn(question))
        self.wait(1.2)
        self.clear_scene()

    def walk_the_track(self):
        # Narration: Pretend to drive. Each segment turns the heading a little,
        # then takes one step forward. The trail is the map.
        heading = make_heading("2  Walk the segments and leave a trail", HEADING)
        code = code_block(
            [
                "for curve, _ in track:",
                "    heading += radians(curve * 0.2)",
                "    x += sin(heading)",
                "    y -= cos(heading)",
                "    points.append((x, y))",
            ],
            [-3.7, 0.3, 0],
            22,
        )
        code_panel = make_panel(6.4, 3.2, code.get_center())
        scale_note = make_text(
            "TURN_DEGREES_PER_CURVE = 0.2", 22, EASING, "BOLD"
        ).next_to(code_panel, DOWN, buff=0.35)
        map_panel = make_panel(6.4, 5.0, [3.55, -0.3, 0])
        points = fit(TRACK_POINTS, 5.6, 2.6, map_panel.get_center())
        step = 40
        stride_note = make_text(
            f"(one dot every {step} segments)", 20, MUTED
        ).next_to(map_panel, DOWN, buff=0.25)

        self.play(Write(heading))
        self.play(FadeIn(code_panel), FadeIn(code), FadeIn(map_panel))
        self.play(FadeIn(scale_note), FadeIn(stride_note))

        turn_box = SurroundingRectangle(code[1], color=HEADING, buff=0.08)
        step_box = SurroundingRectangle(VGroup(code[2], code[3]), color=PATH, buff=0.08)
        walker = Dot(points[0], radius=0.09, color=HEADING)
        arrow = Arrow(points[0], points[0] + RIGHT * 0.6, buff=0, color=HEADING)
        self.play(FadeIn(walker), FadeIn(arrow), Create(turn_box))
        self.play(Transform(turn_box, step_box))

        trail = VGroup()
        for index in range(step, len(points), step):
            direction = points[index] - points[index - step]
            direction = direction / np.linalg.norm(direction) * 0.6
            new_arrow = Arrow(points[index], points[index] + direction, buff=0, color=HEADING)
            trail.add(Dot(points[index - step], radius=0.04, color=PATH))
            self.add(trail[-1])
            self.play(
                walker.animate.move_to(points[index]),
                Transform(arrow, new_arrow),
                run_time=0.09,
            )
        oval = polyline(points, PATH, 5)
        self.play(FadeOut(walker), FadeOut(arrow), FadeOut(turn_box), Create(oval), run_time=1.4)
        done = make_text("2280 steps later: the oval", 24, PATH, "BOLD").next_to(
            map_panel, UP, buff=0.18
        )
        self.play(FadeIn(done))
        self.wait(1.0)
        self.clear_scene()

    def two_rules_for_a_loop(self):
        # Narration: A loop needs two things: total turning of one full turn,
        # and an end point that lands on the start. The old track only had the
        # first one.
        heading = make_heading("3  Two rules for a closed loop", WARNING)
        rule1 = make_text("1. total turning = 360°", 27, TEXT, "BOLD")
        rule2 = make_text("2. end point = start point", 27, TEXT, "BOLD")
        rules = VGroup(rule1, rule2).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        rules.move_to([-4.0, 1.4, 0])

        old = old_track()
        old_scale = 360 / abs(sum(curve for curve, _ in old))
        old_points = fit(walk(old, old_scale), 5.6, 4.3, [2.9, -0.4, 0])
        old_path = polyline(old_points, SEGMENT, 5)
        start = Dot(old_points[0], radius=0.11, color=PATH)
        end = Dot(old_points[-1], radius=0.11, color=WARNING)
        start_label = make_text("start", 20, PATH).next_to(start, UP, buff=0.12)
        end_label = make_text("end", 20, WARNING).next_to(end, DOWN, buff=0.12)
        gap = DashedLine(old_points[-1], old_points[0], color=WARNING, stroke_width=4)
        old_title = make_text("old track, scaled to turn 360°", 22, MUTED).next_to(
            old_path, UP, buff=0.25
        )
        check1 = make_text("✓ facing the start direction", 24, PATH).move_to([-4.0, -0.4, 0])
        check2 = make_text("✗ gap as big as the track", 24, WARNING).next_to(
            check1, DOWN, aligned_edge=LEFT, buff=0.3
        )
        why = make_text(
            "long straights first, bends bunched later → it spirals off",
            21,
            MUTED,
        ).to_edge(DOWN, buff=0.5)

        self.play(Write(heading))
        self.play(FadeIn(rules))
        self.play(FadeIn(old_title), Create(old_path), run_time=2.4)
        self.play(FadeIn(start), FadeIn(start_label), FadeIn(end), FadeIn(end_label))
        self.play(FadeIn(check1))
        self.play(Create(gap), FadeIn(check2))
        self.play(FadeIn(why))
        self.wait(1.4)
        self.clear_scene()

    def two_identical_halves(self):
        # Narration: Build half a lap that turns 180 degrees, then add the same
        # half again. Rotating a half by 180 degrees around the middle of its
        # ends swaps its start and end, so the second half lands on the start.
        heading = make_heading("4  Two identical halves always close", PATH)
        code = code_block(
            ["def build_track():", "    add_half_lap(track)", "    add_half_lap(track)"],
            [-4.4, 1.5, 0],
            22,
        )
        points = fit(TRACK_POINTS, 6.6, 2.4, [2.4, -0.6, 0])
        first = polyline(points[: HALF + 1], SEGMENT, 7)
        a, b = points[0], points[HALF]
        dot_a = Dot(a, radius=0.11, color=TEXT)
        dot_b = Dot(b, radius=0.11, color=TEXT)
        label_a = make_text("A: start", 20, TEXT).next_to(dot_a, UP, buff=0.15)
        label_b = make_text("B: half-way", 20, TEXT).next_to(dot_b, DOWN, buff=0.15)
        middle = (a + b) / 2
        pivot = Dot(middle, radius=0.07, color=EASING)
        pivot_label = make_text("pivot", 19, EASING).next_to(pivot, RIGHT, buff=0.12)
        half_note = make_text("half lap: straight + 180° bend", 22, SEGMENT).move_to(
            [-4.4, 0.0, 0]
        )
        spin_note = make_text("copy, spin 180° about the pivot:", 22, CURVE).move_to(
            [-4.4, -0.7, 0]
        )
        swap_note = make_text("A ↔ B swap places", 22, CURVE, "BOLD").next_to(
            spin_note, DOWN, buff=0.25
        )
        closed = make_text("second half ends exactly at A", 24, PATH, "BOLD").to_edge(
            DOWN, buff=0.5
        )

        self.play(Write(heading), FadeIn(code))
        self.play(Create(first), FadeIn(half_note), run_time=1.8)
        self.play(FadeIn(dot_a), FadeIn(label_a), FadeIn(dot_b), FadeIn(label_b))
        self.play(FadeIn(pivot), FadeIn(pivot_label))
        second = first.copy().set_stroke(CURVE, 7)
        self.add(second)
        self.play(FadeIn(spin_note))
        self.play(second.animate.rotate(PI, about_point=middle), run_time=2.4)
        self.play(FadeIn(swap_note), FadeIn(closed))
        self.wait(1.4)
        self.clear_scene()

    def add_corner_math(self):
        # Narration: add_corner gets a target angle and works backwards to
        # the curve value. Easing means the entry and exit count for less than
        # full segments.
        enter, hold, leave = 60, 420, 60
        enter_share = sum(GAME.ease_in(0.0, 1.0, i / enter) for i in range(enter))
        leave_share = sum(GAME.ease_in_out(1.0, 0.0, i / leave) for i in range(leave))
        total = enter_share + hold + leave_share
        curve = 180 / GAME.TURN_DEGREES_PER_CURVE / total

        heading = make_heading("5  add_corner: start from the angle you want", EASING)
        corner = TRACK[HALF - enter - hold - leave : HALF]
        base_y, height, width = -1.0, 2.2, 11.0
        left = -width / 2
        bars = VGroup()
        for index, (value, _) in enumerate(corner):
            if index % 4:
                continue
            x = left + width * index / len(corner)
            color = EASING if index < enter or index >= enter + hold else CURVE
            bars.add(
                Line(
                    [x, base_y, 0],
                    [x, base_y + height * value / curve, 0],
                    color=color,
                    stroke_width=4,
                )
            )
        axis = Line([left, base_y, 0], [left + width, base_y, 0], color=MUTED)

        def phase_label(content, start, length, color):
            middle = left + width * (start + length / 2) / len(corner)
            return make_text(content, 20, color).move_to([middle, base_y - 0.4, 0])

        labels = VGroup(
            phase_label(f"enter 60 → counts as {enter_share:.1f}", 0, enter, EASING),
            phase_label(f"hold 420 → counts as 420", enter, hold, CURVE),
            phase_label(f"leave 60 → {leave_share:.1f}", enter + hold, leave, EASING),
        )
        formula = make_code(
            f"curve = 180 / 0.2 / ({enter_share:.1f} + 420 + {leave_share:.1f})",
            24,
        ).move_to([0, 2.0, 0])
        result = make_code(f"      = 900 / {total:.0f} = {curve:.3f}", 24, CURVE).next_to(
            formula, DOWN, aligned_edge=LEFT, buff=0.22
        )
        footer = make_text(
            "Same easing functions as add_road, so the bend turns exactly 180°",
            22,
            MUTED,
        ).to_edge(DOWN, buff=0.45)

        self.play(Write(heading))
        self.play(Create(axis), FadeIn(bars, lag_ratio=0.02), run_time=2.0)
        self.play(FadeIn(labels))
        self.play(FadeIn(formula))
        self.play(FadeIn(result))
        self.play(FadeIn(footer))
        self.wait(1.6)
        self.clear_scene()

    def cache_and_player_dot(self):
        # Narration: The outline is drawn once at startup. Each frame only
        # places the dot, blending between two stored points.
        heading = make_heading("6  Draw once, then just move the dot", PLAYER)
        once = make_text("startup: build_minimap(track) → surface", 23, PATH, "BOLD")
        every = make_text("every frame: blit surface + draw dot", 23, SEGMENT, "BOLD")
        VGroup(once, every).arrange(DOWN, aligned_edge=LEFT, buff=0.25).move_to(
            [-3.4, 2.0, 0]
        )
        box = make_panel(3.4, 3.4, [4.6, 1.0, 0])
        mini = polyline(fit(TRACK_POINTS, 3.0, 1.0, box.get_center()), TEXT, 4)

        index = 802
        near = np.array([-4.5, -1.6, 0])
        far = np.array([0.5, -1.6, 0])
        segment = Line(near, far, color=MUTED, stroke_width=4)
        near_dot = Dot(near, radius=0.1, color=TEXT)
        far_dot = Dot(far, radius=0.1, color=TEXT)
        near_label = make_code(f"path[{index}]", 20, TEXT).next_to(near_dot, DOWN, buff=0.2)
        far_label = make_code(f"path[{index + 1}]", 20, TEXT).next_to(far_dot, DOWN, buff=0.2)

        percent = ValueTracker(0.0)
        player = always_redraw(
            lambda: Dot(
                near + (far - near) * percent.get_value(),
                radius=0.16,
                color=PLAYER,
            )
        )
        readout = always_redraw(
            lambda: make_code(
                f"segment_position = {index + percent.get_value():.2f}\n"
                f"index   = int(...)  = {index}\n"
                f"percent = ... % 1   = {percent.get_value():.2f}",
                21,
            ).move_to([-2.0, -0.2, 0])
        )
        lerp = make_code("dot = near + (far - near) * percent", 22, EASING).move_to(
            [-2.0, -2.7, 0]
        )

        self.play(Write(heading))
        self.play(FadeIn(once), FadeIn(box), Create(mini))
        self.play(FadeIn(every))
        self.play(
            Create(segment),
            FadeIn(near_dot),
            FadeIn(far_dot),
            FadeIn(near_label),
            FadeIn(far_label),
        )
        self.play(FadeIn(player), FadeIn(readout))
        self.play(percent.animate.set_value(0.5), run_time=1.6)
        self.wait(0.5)
        self.play(FadeIn(lerp))
        self.play(percent.animate.set_value(0.99), run_time=1.6)
        self.wait(1.0)
        self.clear_scene()

    def recap(self):
        # Narration: Curves become a heading, headings become a trail, two
        # halves close the loop, and a cached map just needs a moving dot.
        heading = make_heading("Recap", TEXT)
        steps = VGroup(
            make_text("1. curve × 0.2° turns the heading", 26, HEADING),
            make_text("2. one step per segment leaves the trail", 26, PATH),
            make_text("3. loop = 360° turn AND end on the start", 26, WARNING),
            make_text("4. two identical 180° halves guarantee both", 26, SEGMENT),
            make_text("5. add_corner works the curve out from the angle", 26, EASING),
            make_text("6. cache the map, interpolate the dot", 26, PLAYER),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.28)
        steps.move_to([-1.6, -0.3, 0])
        oval = polyline(fit(TRACK_POINTS, 3.0, 1.0, [4.8, -0.3, 0]), PATH, 5)
        self.play(Write(heading))
        self.play(FadeIn(steps, lag_ratio=0.25), Create(oval), run_time=3.0)
        self.wait(2.0)
