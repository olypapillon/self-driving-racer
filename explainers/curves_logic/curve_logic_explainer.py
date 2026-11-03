import math
from pathlib import Path

from manim import (
    Arrow,
    Circle,
    Create,
    DashedLine,
    Dot,
    DOWN,
    FadeIn,
    FadeOut,
    Group,
    GrowArrow,
    ImageMobject,
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
    VGroup,
    VMobject,
    WHITE,
    Write,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CAR_IMAGE_PATH = PROJECT_ROOT / "assets" / "car-rear.png"

BACKGROUND = "#0B1020"
PANEL = "#151D32"
TEXT = "#ECF2FF"
MUTED = "#9FB0CF"
SEGMENT = "#58A6FF"
CURVE = "#FF8A65"
DIRECTION = "#C297FF"
OFFSET = "#63D297"
EASING = "#F2CC60"
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


def make_perspective_road(bend=0.0, lateral=0.0):
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
        centers.append(-lateral * (1 - percent) + bend * percent**2)

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


def make_overhead_road(bend=0.0, color=ROAD_LIGHT):
    levels = 8
    bottom_y = -2.2
    top_y = 2.2
    half_width = 0.76
    centers = [bend * (index / levels) ** 2 for index in range(levels + 1)]
    ys = [bottom_y + (top_y - bottom_y) * index / levels for index in range(levels + 1)]

    road = VGroup()
    for index in range(levels):
        road.add(
            Polygon(
                [centers[index] - half_width, ys[index], 0],
                [centers[index] + half_width, ys[index], 0],
                [centers[index + 1] + half_width, ys[index + 1], 0],
                [centers[index + 1] - half_width, ys[index + 1], 0],
                fill_color=color if index % 2 else ROAD_DARK,
                fill_opacity=1,
                stroke_color=BACKGROUND,
                stroke_width=1.5,
            )
        )
    return road


def make_value_box(label, color, width=3.3):
    box = RoundedRectangle(
        width=width,
        height=0.88,
        corner_radius=0.14,
        stroke_color=color,
        stroke_width=2,
        fill_color=color,
        fill_opacity=0.12,
    )
    text = make_text(label, 25, color, "BOLD").move_to(box)
    return VGroup(box, text)


class CurveLogicExplainer(Scene):
    def construct(self):
        self.camera.background_color = BACKGROUND

        # Learning goal: Understand how per-segment curve values become a
        # convincing pseudo-3D bend without constructing true curved geometry.
        # Narration: This road does not bend in 3D; it creates the appearance of
        # a bend by shifting the center of each projected segment.
        title = make_text("How pseudo-3D road curves work", 48, TEXT, "BOLD")
        subtitle = make_text(
            "The visual logic behind segment curves, easing, x, and dx",
            27,
            MUTED,
        ).next_to(title, DOWN, buff=0.28)
        straight_intro = make_perspective_road(0.0).scale(0.55).shift(DOWN * 0.75)
        curved_intro = make_perspective_road(1.65).scale(0.55).shift(DOWN * 0.75)
        center_hint = make_text("shift successive segment centers", 23, OFFSET, "BOLD")
        center_hint.to_edge(DOWN, buff=0.42)

        self.play(Write(title), FadeIn(subtitle))
        self.play(FadeIn(straight_intro))
        self.play(Transform(straight_intro, curved_intro), FadeIn(center_hint), run_time=2.1)
        self.wait(0.8)
        self.play(FadeOut(VGroup(title, subtitle, straight_intro, center_hint)))

        # Section 1
        # Narration: Full 3D would calculate a curved strip in world space, but
        # the pseudo-3D trick keeps simple segments and moves their screen centers.
        heading1 = make_heading("1  Fake the center line, not the 3D geometry", SEGMENT)
        left_panel = make_panel(5.5, 5.2, [-3.65, -0.25, 0])
        right_panel = make_panel(5.5, 5.2, [3.65, -0.25, 0])
        left_title = make_text("Full 3D idea", 25, TEXT, "BOLD").move_to([-3.65, 2.0, 0])
        right_title = make_text("Pseudo-3D trick", 25, TEXT, "BOLD").move_to([3.65, 2.0, 0])

        true_curve = make_overhead_road(1.25).scale(0.82).move_to([-3.75, -0.25, 0])
        true_caption = make_text("calculate world x and z", 21, MUTED).move_to([-3.65, -2.3, 0])

        shifted_slices = VGroup()
        for index in range(7):
            y = -1.85 + index * 0.55
            width = 4.0 - index * 0.43
            center = 2.9 + 0.11 * index**2
            shifted_slices.add(
                Line(
                    [center - width / 2, y, 0],
                    [center + width / 2, y, 0],
                    color=ROAD_LIGHT if index % 2 else ROAD_DARK,
                    stroke_width=18,
                )
            )
        fake_caption = make_text("move each projected center", 21, OFFSET, "BOLD")
        fake_caption.move_to([3.65, -2.3, 0])
        shift_arrow = Arrow([3.65, 0.0, 0], [4.8, 0.0, 0], color=OFFSET, stroke_width=5)

        self.play(
            FadeIn(heading1),
            FadeIn(left_panel),
            FadeIn(right_panel),
            FadeIn(left_title),
            FadeIn(true_curve),
            FadeIn(true_caption),
        )
        self.play(FadeIn(right_title), FadeIn(shifted_slices), GrowArrow(shift_arrow), FadeIn(fake_caption))
        self.wait(1.0)
        self.play(
            FadeOut(
                VGroup(
                    heading1,
                    left_panel,
                    right_panel,
                    left_title,
                    right_title,
                    true_curve,
                    true_caption,
                    shifted_slices,
                    fake_caption,
                    shift_arrow,
                )
            )
        )

        # Section 2
        # Narration: Every segment stores one signed strength: the sign chooses
        # left or right, and the magnitude chooses how hard the road turns.
        heading2 = make_heading("2  One signed curve value per segment", CURVE)
        values = [0, 0, 1, 2, 3, 3, 2, 1, 0]
        cards = VGroup()
        for value in values:
            color = MUTED if value == 0 else CURVE
            card = RoundedRectangle(
                width=1.15,
                height=1.15,
                corner_radius=0.1,
                stroke_color=color,
                fill_color=color,
                fill_opacity=0.12,
            )
            label = make_text(f"{value:+d}" if value else "0", 26, color, "BOLD").move_to(card)
            cards.add(VGroup(card, label))
        cards.arrange(RIGHT, buff=0.16).move_to([0, 0.65, 0])
        segment_label = make_text("successive road segments", 22, MUTED).next_to(cards, UP, buff=0.28)

        sign_box = make_value_box("sign  ->  left or right", SEGMENT, 4.7).move_to([-3.0, -1.45, 0])
        strength_box = make_value_box("magnitude  ->  turn strength", CURVE, 5.4).move_to([3.0, -1.45, 0])
        left_example = make_text("-3  bends left", 22, SEGMENT, "BOLD").move_to([-3.0, -2.55, 0])
        right_example = make_text("+3  bends right", 22, CURVE, "BOLD").move_to([3.0, -2.55, 0])

        self.play(FadeIn(heading2), FadeIn(segment_label))
        for card in cards:
            self.play(FadeIn(card, shift=UP * 0.12), run_time=0.18)
        self.play(FadeIn(sign_box), FadeIn(strength_box))
        self.play(FadeIn(left_example), FadeIn(right_example))
        self.wait(0.9)
        self.play(
            FadeOut(
                VGroup(
                    heading2,
                    cards,
                    segment_label,
                    sign_box,
                    strength_box,
                    left_example,
                    right_example,
                )
            )
        )

        # Section 3
        # Narration: Curve strength rises gradually, holds, and falls gradually,
        # preventing the road from snapping sideways at segment boundaries.
        heading3 = make_heading("3  Ease into, hold, and ease out of the turn", EASING)
        x_axis = Line([-5.8, -2.1, 0], [5.8, -2.1, 0], color=MUTED, stroke_width=3)
        y_axis = Line([-5.8, -2.1, 0], [-5.8, 1.75, 0], color=MUTED, stroke_width=3)
        progress_label = make_text("segments along the road", 21, MUTED).next_to(x_axis, DOWN, buff=0.22)
        strength_label = make_text("curve strength", 21, MUTED).rotate(1.5708)
        strength_label.next_to(y_axis, LEFT, buff=0.22)

        graph_points = []
        sample_count = 36
        for index in range(sample_count + 1):
            percent = index / sample_count
            x = -5.45 + percent * 10.9
            if percent < 1 / 3:
                local = percent * 3
                value = local**2
            elif percent < 2 / 3:
                value = 1.0
            else:
                local = (percent - 2 / 3) * 3
                value = (1 + math.cos(local * math.pi)) / 2
            y = -2.1 + value * 3.25
            graph_points.append([x, y, 0])
        curve_graph = VMobject(color=EASING, stroke_width=6).set_points_smoothly(graph_points)
        enter_line = DashedLine([-1.82, -2.1, 0], [-1.82, 1.4, 0], color="#45516F")
        leave_line = DashedLine([1.82, -2.1, 0], [1.82, 1.4, 0], color="#45516F")
        phase_labels = VGroup(
            make_text("ease in", 23, EASING, "BOLD").move_to([-3.65, 1.75, 0]),
            make_text("hold", 23, EASING, "BOLD").move_to([0, 1.75, 0]),
            make_text("ease out", 23, EASING, "BOLD").move_to([3.65, 1.75, 0]),
        )
        smooth_note = make_text("smooth changes prevent a visible snap", 24, TEXT, "BOLD")
        smooth_note.to_edge(DOWN, buff=0.4)

        self.play(FadeIn(heading3), Create(x_axis), Create(y_axis))
        self.play(FadeIn(progress_label), FadeIn(strength_label), FadeIn(phase_labels))
        self.play(Create(curve_graph), Create(enter_line), Create(leave_line), run_time=2.2)
        self.play(FadeIn(smooth_note))
        self.wait(0.9)
        self.play(
            FadeOut(
                VGroup(
                    heading3,
                    x_axis,
                    y_axis,
                    progress_label,
                    strength_label,
                    curve_graph,
                    enter_line,
                    leave_line,
                    phase_labels,
                    smooth_note,
                )
            )
        )

        # Section 4
        # Narration: Curvature changes the sideways direction dx; that direction
        # changes the center position x, so the bend requires two accumulations.
        heading4 = make_heading("4  Curvature changes direction; direction changes position", DIRECTION)
        curve_box = make_value_box("curve: +1 each segment", CURVE, 3.7).move_to([-4.8, 1.6, 0])
        dx_box = make_value_box("dx:  0, 1, 2, 3, 4", DIRECTION, 3.6).move_to([0, 1.6, 0])
        x_box = make_value_box("x:  0, 0, 1, 3, 6", OFFSET, 3.6).move_to([4.8, 1.6, 0])
        first_arrow = Arrow(curve_box.get_right(), dx_box.get_left(), buff=0.14, color=MUTED)
        second_arrow = Arrow(dx_box.get_right(), x_box.get_left(), buff=0.14, color=MUTED)
        first_label = make_text("1st accumulation", 18, MUTED).next_to(first_arrow, UP, buff=0.08)
        second_label = make_text("2nd accumulation", 18, MUTED).next_to(second_arrow, UP, buff=0.08)

        base_x = -1.2
        center_values = [0.0, 0.0, 0.45, 1.25, 2.4]
        center_dots = VGroup()
        guide_lines = VGroup()
        for index, value in enumerate(center_values):
            y = -2.45 + index * 0.68
            guide_lines.add(Line([-3.7, y, 0], [4.7, y, 0], color="#26324B", stroke_width=2))
            center_dots.add(Dot([base_x + value, y, 0], radius=0.11, color=OFFSET))
        center_path = VMobject(color=OFFSET, stroke_width=5).set_points_smoothly(
            [dot.get_center() for dot in center_dots]
        )
        zero_line = DashedLine([base_x, -2.75, 0], [base_x, 0.65, 0], color=MUTED, dash_length=0.13)
        dx_note = make_text("dx = sideways rate", 22, DIRECTION, "BOLD").move_to([-4.5, -1.0, 0])
        x_note = make_text("x = center offset", 22, OFFSET, "BOLD").move_to([3.85, -1.0, 0])

        self.play(FadeIn(heading4), FadeIn(curve_box))
        self.play(GrowArrow(first_arrow), FadeIn(first_label), FadeIn(dx_box))
        self.play(GrowArrow(second_arrow), FadeIn(second_label), FadeIn(x_box))
        self.play(FadeIn(guide_lines), Create(zero_line), FadeIn(dx_note), FadeIn(x_note))
        for dot in center_dots:
            self.play(FadeIn(dot), run_time=0.25)
        self.play(Create(center_path), run_time=1.2)
        self.wait(1.0)
        self.play(
            FadeOut(
                VGroup(
                    heading4,
                    curve_box,
                    dx_box,
                    x_box,
                    first_arrow,
                    second_arrow,
                    first_label,
                    second_label,
                    center_dots,
                    guide_lines,
                    center_path,
                    zero_line,
                    dx_note,
                    x_note,
                )
            )
        )

        # Section 5
        # Narration: Those accumulated x values shift farther road segments more,
        # and perspective makes the sequence read as one continuous curve.
        heading5 = make_heading("5  Project the shifted centers into perspective", OFFSET)
        straight_road = make_perspective_road(0.0).scale(0.82).shift(DOWN * 0.35)
        curved_road = make_perspective_road(1.7).scale(0.82).shift(DOWN * 0.35)
        camera = Polygon(
            [-0.28, -2.92, 0], [0.28, -2.92, 0], [0, -2.48, 0],
            fill_color=SEGMENT,
            fill_opacity=1,
            stroke_width=0,
        )
        camera_label = make_text("camera", 18, SEGMENT, "BOLD").move_to([0, -3.16, 0])
        near_note = make_text("near: little offset", 20, TEXT, "BOLD").move_to([-4.7, -2.55, 0])
        far_note = make_text("farther: more offset", 20, OFFSET, "BOLD").move_to([4.4, 1.25, 0])
        far_arrow = Arrow([3.55, 1.15, 0], [1.5, 0.85, 0], color=OFFSET, stroke_width=4)
        illusion_note = make_text("the eye joins the slices into one bend", 25, EASING, "BOLD")
        illusion_panel = RoundedRectangle(
            width=6.5,
            height=0.62,
            corner_radius=0.12,
            stroke_width=0,
            fill_color=BACKGROUND,
            fill_opacity=0.88,
        ).move_to([0, 2.18, 0])
        illusion_note.move_to(illusion_panel)

        self.play(FadeIn(heading5), FadeIn(straight_road), FadeIn(camera), FadeIn(camera_label))
        self.play(Transform(straight_road, curved_road), FadeIn(near_note), run_time=2.1)
        self.play(
            FadeIn(far_note),
            GrowArrow(far_arrow),
            FadeIn(illusion_panel),
            FadeIn(illusion_note),
        )
        self.wait(1.0)
        self.play(
            FadeOut(
                VGroup(
                    heading5,
                    straight_road,
                    camera,
                    camera_label,
                    near_note,
                    far_note,
                    far_arrow,
                    illusion_panel,
                    illusion_note,
                )
            )
        )

        # Section 6
        # Narration: Outward player drift and layered background motion complete
        # the illusion, with nearby scenery moving more than distant scenery.
        sky = Rectangle(width=14.25, height=3.5, stroke_width=0, fill_color=SKY, fill_opacity=1).move_to([0, 1.65, 0])
        grass = Rectangle(width=14.25, height=3.8, stroke_width=0, fill_color=GRASS, fill_opacity=1).move_to([0, -1.95, 0])
        heading6 = make_heading("6  Complete the illusion", BACKGROUND)
        hills = VGroup(
            Polygon([-6.8, 0.2, 0], [-4.8, 1.65, 0], [-2.8, 0.2, 0], fill_color="#6C7F8F", fill_opacity=1, stroke_width=0),
            Polygon([-3.8, 0.2, 0], [-1.3, 1.35, 0], [1.0, 0.2, 0], fill_color="#7F93A3", fill_opacity=1, stroke_width=0),
            Polygon([0.2, 0.2, 0], [3.0, 1.5, 0], [5.8, 0.2, 0], fill_color="#6C7F8F", fill_opacity=1, stroke_width=0),
        )
        trees = VGroup(*[
            Circle(radius=0.18, fill_color="#0E4E2A", fill_opacity=1, stroke_width=0).move_to([x, 0.0, 0])
            for x in (-6.2, -5.4, -4.5, 4.4, 5.3, 6.2)
        ])
        final_road = make_perspective_road(1.25)
        car = ImageMobject(str(CAR_IMAGE_PATH))
        car.width = 2.0
        car.move_to([0, -2.72, 0])
        outward_arrow = Arrow([0, -2.15, 0], [-1.25, -2.15, 0], color=CURVE, stroke_width=6)
        outward_label = make_text("outward drift grows with speed and curve", 21, BACKGROUND, "BOLD")
        outward_label.move_to([-3.65, 2.2, 0])

        parallax_panel = RoundedRectangle(
            width=4.8,
            height=1.72,
            corner_radius=0.12,
            stroke_color=BACKGROUND,
            fill_color=TEXT,
            fill_opacity=0.84,
        ).move_to([3.85, 2.0, 0])
        parallax_labels = VGroup(
            make_text("sky", 18, BACKGROUND, "BOLD"),
            make_text("hills", 18, BACKGROUND, "BOLD"),
            make_text("trees", 18, BACKGROUND, "BOLD"),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.15).move_to([2.65, 2.0, 0])
        parallax_arrows = VGroup(
            Arrow([3.15, 2.35, 0], [3.65, 2.35, 0], color=SEGMENT, buff=0, stroke_width=4),
            Arrow([3.15, 2.0, 0], [4.05, 2.0, 0], color=DIRECTION, buff=0, stroke_width=4),
            Arrow([3.15, 1.65, 0], [4.55, 1.65, 0], color=CURVE, buff=0, stroke_width=4),
        )
        parallax_note = make_text("near layers slide farther", 17, BACKGROUND, "BOLD").move_to([4.55, 1.25, 0])

        self.play(FadeIn(sky), FadeIn(grass), FadeIn(hills), FadeIn(trees), FadeIn(final_road), FadeIn(heading6))
        self.play(FadeIn(car), GrowArrow(outward_arrow), FadeIn(outward_label))
        self.play(FadeIn(parallax_panel), FadeIn(parallax_labels), FadeIn(parallax_arrows), FadeIn(parallax_note))
        self.play(car.animate.shift(LEFT * 0.55), hills.animate.shift(RIGHT * 0.18), trees.animate.shift(RIGHT * 0.42), run_time=1.5)
        self.wait(0.9)
        self.play(
            FadeOut(
                Group(
                    sky,
                    grass,
                    heading6,
                    hills,
                    trees,
                    final_road,
                    car,
                    outward_arrow,
                    outward_label,
                    parallax_panel,
                    parallax_labels,
                    parallax_arrows,
                    parallax_note,
                )
            )
        )

        # Recap
        # Narration: A signed curve changes dx, dx changes x, and perspective
        # turns the accumulated center offsets into a convincing road bend.
        recap_title = make_text("The complete curve illusion", 45, TEXT, "BOLD")
        recap_title.to_edge(UP, buff=0.62)
        recap = VGroup(
            make_text("1   assign a signed curve strength to each segment", 27, CURVE),
            make_text("2   ease the strength in, hold it, then ease it out", 27, EASING),
            make_text("3   accumulate curve into dx: sideways direction", 27, DIRECTION),
            make_text("4   accumulate dx into x: center position", 27, OFFSET),
            make_text("5   project the shifted centers and add motion cues", 27, SEGMENT),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.37).move_to([0, -0.15, 0])
        final_line = make_text("curve  ->  dx  ->  x  ->  projected bend", 31, TEXT, "BOLD")
        final_line.to_edge(DOWN, buff=0.55)

        self.play(Write(recap_title))
        self.play(FadeIn(recap, shift=UP * 0.2))
        self.play(FadeIn(final_line))
        self.wait(2.0)
