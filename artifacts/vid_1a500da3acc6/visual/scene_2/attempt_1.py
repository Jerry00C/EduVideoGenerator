from manim import *


class Scene2Scene(Scene):
    def construct(self):
        self.camera.background_color = "#111827"

        def make_atom(color, position):
            atom = Circle(radius=0.58, color=WHITE, stroke_width=3)
            atom.set_fill(color, opacity=0.9)
            atom.move_to(position)
            atom.set_z_index(3)
            return atom

        def make_heading(text):
            heading = Text(text, font_size=38, color=WHITE)
            heading.to_edge(UP, buff=0.45)
            heading.set_z_index(10)
            return heading

        left_atom = make_atom(BLUE_D, LEFT * 4 + DOWN * 0.1)
        right_atom = make_atom(ORANGE, RIGHT * 4 + DOWN * 0.1)
        heading = make_heading("Atoms can bond")

        bond_zone = DashedVMobject(
            Circle(radius=0.43, color=YELLOW, stroke_width=5),
            num_dashes=18,
        )
        bond_zone.move_to(DOWN * 0.1)
        bond_zone.set_z_index(2)

        self.play(Write(heading), FadeIn(left_atom), FadeIn(right_atom), run_time=1.2)
        self.play(
            left_atom.animate.move_to(LEFT * 1.25 + DOWN * 0.1),
            right_atom.animate.move_to(RIGHT * 1.25 + DOWN * 0.1),
            Create(bond_zone),
            run_time=2.4,
        )
        self.play(Indicate(bond_zone, color=YELLOW), run_time=1.2)
        self.wait(2.5)

        new_heading = make_heading("Bonded atoms form a molecule")
        bond_line = Line(
            left_atom.get_center() + RIGHT * 0.58,
            right_atom.get_center() + LEFT * 0.58,
            color=LIGHT_GREY,
            stroke_width=14,
        )
        bond_line.set_z_index(1)

        outline = RoundedRectangle(
            width=3.7,
            height=1.65,
            corner_radius=0.35,
            color=GREEN_C,
            stroke_width=4,
        )
        outline.move_to(DOWN * 0.1)
        outline.set_fill(GREEN_E, opacity=0.08)
        outline.set_z_index(0)

        self.play(
            ReplacementTransform(heading, new_heading),
            FadeOut(bond_zone),
            Create(bond_line),
            run_time=1.5,
        )
        heading = new_heading
        self.play(Create(outline), run_time=1.2)
        self.bring_to_front(left_atom, right_atom)
        molecule_group = VGroup(outline, bond_line, left_atom, right_atom)
        self.wait(3)

        new_heading = make_heading("Molecule: 2 or more bonded atoms")
        left_label = Text("atom", font_size=26, color=BLUE_B).move_to(LEFT * 2.8 + UP * 1.35)
        right_label = Text("atom", font_size=26, color=ORANGE).move_to(RIGHT * 2.8 + UP * 1.35)
        bond_label = Text("bond", font_size=26, color=YELLOW).move_to(DOWN * 1.65)

        left_arrow = Arrow(
            left_label.get_bottom(),
            left_atom.get_center() + UP * 0.35,
            buff=0.12,
            color=BLUE_B,
            stroke_width=3,
            max_tip_length_to_length_ratio=0.12,
        )
        right_arrow = Arrow(
            right_label.get_bottom(),
            right_atom.get_center() + UP * 0.35,
            buff=0.12,
            color=ORANGE,
            stroke_width=3,
            max_tip_length_to_length_ratio=0.12,
        )
        bond_arrow = Arrow(
            bond_label.get_top(),
            bond_line.get_center(),
            buff=0.12,
            color=YELLOW,
            stroke_width=3,
            max_tip_length_to_length_ratio=0.12,
        )

        label_group = VGroup(left_label, right_label, bond_label)
        arrow_group = VGroup(left_arrow, right_arrow, bond_arrow)
        label_group.set_z_index(8)
        arrow_group.set_z_index(7)

        self.play(ReplacementTransform(heading, new_heading), run_time=1)
        heading = new_heading
        self.play(
            FadeIn(label_group, shift=UP * 0.15),
            GrowArrow(left_arrow),
            GrowArrow(right_arrow),
            GrowArrow(bond_arrow),
            run_time=2,
        )
        self.wait(4)

        new_heading = make_heading("One atom ≠ molecule")
        single_atom = make_atom(PURPLE_B, LEFT * 3.1 + DOWN * 0.1)

        divider = Line(UP * 1.65, DOWN * 2.0, color=GREY_B, stroke_width=3)
        divider.set_z_index(0)

        molecule_label = Text("molecule", font_size=29, color=GREEN_B)
        molecule_label.move_to(RIGHT * 3.1 + DOWN * 1.45)
        molecule_label.set_z_index(8)

        self.play(
            ReplacementTransform(heading, new_heading),
            FadeOut(label_group),
            FadeOut(arrow_group),
            run_time=1,
        )
        heading = new_heading

        self.play(
            FadeIn(single_atom, shift=RIGHT * 0.2),
            molecule_group.animate.move_to(RIGHT * 3.1 + DOWN * 0.1),
            Create(divider),
            run_time=2,
        )
        self.play(FadeIn(molecule_label), Indicate(outline, color=GREEN_B), run_time=1.6)
        self.wait(4)

        new_heading = make_heading("A bonded distinct unit")
        self.play(
            ReplacementTransform(heading, new_heading),
            FadeOut(single_atom),
            FadeOut(divider),
            FadeOut(molecule_label),
            molecule_group.animate.move_to(DOWN * 0.1),
            run_time=2,
        )
        heading = new_heading

        self.play(outline.animate.set_stroke(YELLOW, width=7).set_fill(YELLOW, opacity=0.08), run_time=1.2)
        self.play(Circumscribe(molecule_group, color=YELLOW, fade_out=True), run_time=1.8)
        self.play(outline.animate.scale(1.06), run_time=1)
        self.play(outline.animate.scale(1 / 1.06), run_time=1)
        self.play(Indicate(molecule_group, color=YELLOW), run_time=1.5)
        self.wait(5)