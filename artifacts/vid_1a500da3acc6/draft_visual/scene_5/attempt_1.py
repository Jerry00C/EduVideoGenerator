from manim import *


class Scene5Scene(Scene):
    def construct(self):
        self.camera.background_color = "#0f1720"

        title = Text("Atom vs. molecule", font_size=44, weight=BOLD, color=WHITE)
        title.to_edge(UP, buff=0.25)

        table_center = DOWN * 0.15
        table_width = 12.2
        table_height = 5.9
        table = RoundedRectangle(
            width=table_width,
            height=table_height,
            corner_radius=0.12,
            stroke_color=BLUE_B,
            stroke_width=3,
            fill_color="#142333",
            fill_opacity=0.55,
        ).move_to(table_center)

        top_y = table.get_top()[1]
        bottom_y = table.get_bottom()[1]
        left_x = table.get_left()[0]
        right_x = table.get_right()[0]

        divider = Line(
            [0, bottom_y, 0],
            [0, top_y, 0],
            color=BLUE_B,
            stroke_width=2.5,
        )
        header_line = Line(
            [left_x, 2.0, 0],
            [right_x, 2.0, 0],
            color=BLUE_B,
            stroke_width=2.5,
        )

        atom_header = Text("Atom", font_size=34, weight=BOLD, color=YELLOW_C)
        molecule_header = Text("Molecule", font_size=34, weight=BOLD, color=TEAL_B)
        atom_header.move_to(LEFT * 3.05 + UP * 2.35)
        molecule_header.move_to(RIGHT * 3.05 + UP * 2.35)

        self.play(Write(title), run_time=0.8)
        self.play(Create(table), Create(divider), Create(header_line), run_time=1.2)
        self.play(FadeIn(atom_header, shift=UP * 0.15), FadeIn(molecule_header, shift=UP * 0.15), run_time=0.8)
        self.wait(1.7)

        atom_icon = self.make_atom_icon().move_to(LEFT * 3.05 + UP * 0.75)
        atom_text = Text("Atom: one unit", font_size=30, color=WHITE).move_to(LEFT * 3.05 + DOWN * 0.45)

        self.play(DrawBorderThenFill(atom_icon), run_time=1.5)
        self.play(Write(atom_text), run_time=0.9)
        self.wait(2.0)

        molecule_icon = self.make_two_atom_molecule().move_to(RIGHT * 3.05 + UP * 0.85)
        molecule_text = Text("Molecule: bonded atoms", font_size=28, color=WHITE)
        molecule_text.move_to(RIGHT * 3.05 + DOWN * 0.25)

        self.play(FadeIn(molecule_icon, scale=0.95), run_time=1.4)
        self.play(Write(molecule_text), run_time=1.0)
        self.wait(2.0)

        o2_label = Text("O2: same element", font_size=25, color=WHITE)
        o2_label.move_to(RIGHT * 2.05 + DOWN * 1.45)

        o2_diagram, o2_highlights = self.make_o2_diagram()
        o2_diagram.move_to(RIGHT * 4.55 + DOWN * 1.45)
        for ring, atom in zip(o2_highlights, [o2_diagram[1], o2_diagram[2]]):
            ring.move_to(atom.get_center())

        self.play(Write(o2_label), FadeIn(o2_diagram, shift=RIGHT * 0.2), run_time=1.2)
        self.play(FadeIn(o2_highlights), run_time=0.5)
        self.play(Indicate(o2_highlights, color=YELLOW), run_time=1.0)
        self.wait(2.6)

        h2o_label = Text("H2O: different elements", font_size=25, color=WHITE)
        h2o_label.move_to(RIGHT * 2.05 + DOWN * 2.55)

        h2o_diagram, h2o_highlights = self.make_h2o_diagram()
        h2o_diagram.move_to(RIGHT * 4.55 + DOWN * 2.55)
        h2o_highlights[0].move_to(h2o_diagram[2].get_center())
        h2o_highlights[1].move_to(h2o_diagram[3].get_center())
        h2o_highlights[2].move_to(h2o_diagram[4].get_center())

        self.play(Write(h2o_label), FadeIn(h2o_diagram, shift=RIGHT * 0.2), run_time=1.2)
        self.play(FadeIn(h2o_highlights), run_time=0.5)
        self.play(Indicate(h2o_highlights, scale_factor=1.08), run_time=1.0)
        self.wait(2.6)

        summary = Text("Atom: one. Molecule: bonded group.", font_size=31, weight=BOLD, color=WHITE)
        summary_bg = RoundedRectangle(
            width=8.7,
            height=0.58,
            corner_radius=0.15,
            fill_color=BLUE_E,
            fill_opacity=0.85,
            stroke_color=BLUE_C,
            stroke_width=2,
        )
        summary_group = VGroup(summary_bg, summary).move_to(DOWN * 3.58)

        self.play(FadeIn(summary_group, shift=UP * 0.15), run_time=1.0)
        self.play(
            Circumscribe(atom_text, color=YELLOW_C, fade_out=True),
            Circumscribe(molecule_text, color=TEAL_B, fade_out=True),
            run_time=1.5,
        )
        self.wait(4.8)

    def make_atom_icon(self):
        nucleus = Circle(
            radius=0.23,
            fill_color=YELLOW_C,
            fill_opacity=1,
            stroke_color=YELLOW_A,
            stroke_width=2,
        )
        orbit1 = Ellipse(width=1.55, height=0.62, stroke_color=BLUE_A, stroke_width=3)
        orbit2 = Ellipse(width=1.55, height=0.62, stroke_color=BLUE_A, stroke_width=3).rotate(PI / 3)
        orbit3 = Ellipse(width=1.55, height=0.62, stroke_color=BLUE_A, stroke_width=3).rotate(-PI / 3)
        electron = Dot(point=RIGHT * 0.78, radius=0.055, color=WHITE)
        return VGroup(orbit1, orbit2, orbit3, nucleus, electron)

    def make_two_atom_molecule(self):
        left_atom = Circle(radius=0.42, fill_color=TEAL_D, fill_opacity=0.9, stroke_color=TEAL_A, stroke_width=3)
        right_atom = Circle(radius=0.42, fill_color=TEAL_D, fill_opacity=0.9, stroke_color=TEAL_A, stroke_width=3)
        left_atom.shift(LEFT * 0.48)
        right_atom.shift(RIGHT * 0.48)
        bond = Line(left_atom.get_center(), right_atom.get_center(), color=GRAY_B, stroke_width=8)
        return VGroup(bond, left_atom, right_atom)

    def labeled_atom(self, symbol, radius, fill_color, text_color=WHITE):
        circle = Circle(
            radius=radius,
            fill_color=fill_color,
            fill_opacity=0.95,
            stroke_color=WHITE,
            stroke_width=2,
        )
        label = Text(symbol, font_size=int(radius * 82), weight=BOLD, color=text_color)
        label.move_to(circle.get_center())
        return VGroup(circle, label)

    def make_o2_diagram(self):
        o1 = self.labeled_atom("O", 0.32, BLUE_D)
        o2 = self.labeled_atom("O", 0.32, BLUE_D)
        o1.shift(LEFT * 0.42)
        o2.shift(RIGHT * 0.42)
        bond = Line(o1.get_center(), o2.get_center(), color=GRAY_B, stroke_width=7)
        diagram = VGroup(bond, o1, o2)

        ring1 = Circle(radius=0.41, stroke_color=YELLOW, stroke_width=4)
        ring2 = Circle(radius=0.41, stroke_color=YELLOW, stroke_width=4)
        highlights = VGroup(ring1, ring2)
        return diagram, highlights

    def make_h2o_diagram(self):
        oxygen = self.labeled_atom("O", 0.34, RED_D)
        hydrogen1 = self.labeled_atom("H", 0.25, GREEN_D)
        hydrogen2 = self.labeled_atom("H", 0.25, GREEN_D)

        oxygen.shift(UP * 0.22)
        hydrogen1.shift(LEFT * 0.55 + DOWN * 0.28)
        hydrogen2.shift(RIGHT * 0.55 + DOWN * 0.28)

        bond1 = Line(oxygen.get_center(), hydrogen1.get_center(), color=GRAY_B, stroke_width=6)
        bond2 = Line(oxygen.get_center(), hydrogen2.get_center(), color=GRAY_B, stroke_width=6)
        diagram = VGroup(bond1, bond2, oxygen, hydrogen1, hydrogen2)

        oxygen_ring = Circle(radius=0.43, stroke_color=ORANGE, stroke_width=4)
        hydrogen_ring1 = Circle(radius=0.33, stroke_color=GREEN_A, stroke_width=4)
        hydrogen_ring2 = Circle(radius=0.33, stroke_color=GREEN_A, stroke_width=4)
        highlights = VGroup(oxygen_ring, hydrogen_ring1, hydrogen_ring2)
        return diagram, highlights