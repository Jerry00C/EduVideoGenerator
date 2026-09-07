from manim import *


class Scene2Scene(Scene):
    def construct(self):
        self.camera.background_color = "#111827"
        self.atom_radius = 0.6

        caption = Text("Atoms can bond", font_size=38, color=WHITE).to_edge(UP, buff=0.45)

        left_atom = self._atom(color=BLUE_C).move_to(LEFT * 4)
        right_atom = self._atom(color=TEAL_C).move_to(RIGHT * 4)

        highlight = DashedVMobject(
            Circle(radius=0.48, color=YELLOW),
            num_dashes=28,
        ).move_to(ORIGIN)
        highlight.set_stroke(width=4)
        highlight.set_z_index(3)

        self.play(FadeIn(caption), FadeIn(left_atom), FadeIn(right_atom), Create(highlight), run_time=1.4)
        self.play(
            left_atom.animate.move_to(LEFT * 1.35),
            right_atom.animate.move_to(RIGHT * 1.35),
            run_time=2.6,
        )
        self.play(Indicate(highlight, color=YELLOW, scale_factor=1.25), run_time=1.6)
        self.wait(3)

        new_caption = Text("Bonded atoms form a molecule", font_size=36, color=WHITE).to_edge(UP, buff=0.45)
        bond = Line(
            left_atom.get_center() + RIGHT * self.atom_radius,
            right_atom.get_center() + LEFT * self.atom_radius,
            color=YELLOW,
            stroke_width=8,
        )
        bond.set_z_index(0)

        molecule_core = VGroup(bond, left_atom, right_atom)
        outline = Ellipse(
            width=molecule_core.width + 0.85,
            height=molecule_core.height + 0.85,
            color=BLUE_B,
            stroke_width=4,
        ).move_to(molecule_core)
        outline.set_fill(BLUE_E, opacity=0.08)
        outline.set_z_index(-1)

        self.play(
            Transform(caption, new_caption),
            FadeOut(highlight),
            Create(bond),
            FadeIn(outline),
            run_time=2.4,
        )
        self.play(Indicate(outline, color=BLUE_B, scale_factor=1.05), run_time=1.4)
        self.wait(3)

        new_caption = Text("Molecule: 2 or more bonded atoms", font_size=34, color=WHITE).to_edge(UP, buff=0.45)

        left_label = Text("atom", font_size=26, color=WHITE).next_to(left_atom, UL, buff=0.45)
        right_label = Text("atom", font_size=26, color=WHITE).next_to(right_atom, UR, buff=0.45)
        bond_label = Text("bond", font_size=26, color=WHITE).next_to(bond, DOWN, buff=0.55)

        left_arrow = Arrow(
            left_label.get_bottom(),
            left_atom.get_center() + UP * 0.32 + LEFT * 0.18,
            buff=0.08,
            color=WHITE,
            stroke_width=3,
            tip_length=0.18,
        )
        right_arrow = Arrow(
            right_label.get_bottom(),
            right_atom.get_center() + UP * 0.32 + RIGHT * 0.18,
            buff=0.08,
            color=WHITE,
            stroke_width=3,
            tip_length=0.18,
        )
        bond_arrow = Arrow(
            bond_label.get_top(),
            bond.get_center(),
            buff=0.08,
            color=WHITE,
            stroke_width=3,
            tip_length=0.18,
        )

        labels = VGroup(left_label, right_label, bond_label, left_arrow, right_arrow, bond_arrow)

        self.play(Transform(caption, new_caption), run_time=1.0)
        self.play(
            LaggedStart(
                FadeIn(left_label), GrowArrow(left_arrow),
                FadeIn(right_label), GrowArrow(right_arrow),
                FadeIn(bond_label), GrowArrow(bond_arrow),
                lag_ratio=0.18,
            ),
            run_time=2.4,
        )
        self.wait(5)

        new_caption = Text("One atom ≠ molecule", font_size=40, color=WHITE).to_edge(UP, buff=0.45)

        old_molecule = VGroup(outline, bond, left_atom, right_atom, labels)

        left_panel = RoundedRectangle(
            width=4.7,
            height=3.5,
            corner_radius=0.22,
            color=GRAY_B,
            stroke_width=2,
        ).move_to(LEFT * 3.2 + DOWN * 0.25)
        left_panel.set_fill(GRAY_E, opacity=0.08)

        right_panel = RoundedRectangle(
            width=4.7,
            height=3.5,
            corner_radius=0.22,
            color=GRAY_B,
            stroke_width=2,
        ).move_to(RIGHT * 3.2 + DOWN * 0.25)
        right_panel.set_fill(GRAY_E, opacity=0.08)

        divider = Line(UP * 1.7, DOWN * 2.1, color=GRAY_B, stroke_width=3)

        single_atom = self._atom(color=BLUE_C, radius=0.62).move_to(LEFT * 3.2 + DOWN * 0.2)

        right_molecule = self._molecule_group(center=RIGHT * 3.2 + DOWN * 0.1, scale_factor=1.0)
        molecule_label = Text("molecule", font_size=28, color=GREEN_B).next_to(right_molecule, DOWN, buff=0.35)

        self.play(
            Transform(caption, new_caption),
            FadeOut(old_molecule),
            run_time=1.2,
        )
        self.play(
            FadeIn(left_panel),
            FadeIn(right_panel),
            Create(divider),
            FadeIn(single_atom),
            FadeIn(right_molecule),
            FadeIn(molecule_label),
            run_time=2.5,
        )
        self.play(Indicate(right_molecule[0], color=GREEN_B, scale_factor=1.06), run_time=1.4)
        self.wait(5)

        new_caption = Text("A bonded distinct unit", font_size=40, color=WHITE).to_edge(UP, buff=0.45)

        self.play(
            Transform(caption, new_caption),
            FadeOut(left_panel),
            FadeOut(right_panel),
            FadeOut(divider),
            FadeOut(single_atom),
            FadeOut(molecule_label),
            right_molecule.animate.move_to(ORIGIN),
            run_time=2.4,
        )

        self.play(Indicate(right_molecule[0], color=YELLOW, scale_factor=1.08), run_time=1.6)
        self.play(right_molecule.animate.shift(RIGHT * 0.55), run_time=1.2)
        self.play(right_molecule.animate.shift(LEFT * 1.1), run_time=1.6)
        self.play(right_molecule.animate.shift(RIGHT * 0.55), run_time=1.2)
        self.play(
            right_molecule[0].animate.set_stroke(YELLOW, width=6),
            rate_func=there_and_back,
            run_time=1.8,
        )
        self.wait(5)

    def _atom(self, color=BLUE_C, radius=None):
        if radius is None:
            radius = self.atom_radius
        body = Circle(radius=radius, color=color, stroke_width=4)
        body.set_fill(color, opacity=0.88)
        shine = Circle(radius=radius * 0.18, color=WHITE, stroke_width=0)
        shine.set_fill(WHITE, opacity=0.35)
        shine.shift(UP * radius * 0.28 + LEFT * radius * 0.25)
        atom = VGroup(body, shine)
        atom.set_z_index(2)
        return atom

    def _molecule_group(self, center=ORIGIN, scale_factor=1.0):
        radius = 0.52 * scale_factor
        sep = 1.62 * scale_factor

        left_atom = self._atom(color=BLUE_C, radius=radius).move_to(center + LEFT * sep / 2)
        right_atom = self._atom(color=TEAL_C, radius=radius).move_to(center + RIGHT * sep / 2)

        bond = Line(
            left_atom.get_center() + RIGHT * radius,
            right_atom.get_center() + LEFT * radius,
            color=YELLOW,
            stroke_width=7 * scale_factor,
        )
        bond.set_z_index(0)

        core = VGroup(bond, left_atom, right_atom)
        outline = Ellipse(
            width=core.width + 0.72 * scale_factor,
            height=core.height + 0.68 * scale_factor,
            color=GREEN_B,
            stroke_width=4,
        ).move_to(core)
        outline.set_fill(GREEN_E, opacity=0.08)
        outline.set_z_index(-1)

        return VGroup(outline, bond, left_atom, right_atom)