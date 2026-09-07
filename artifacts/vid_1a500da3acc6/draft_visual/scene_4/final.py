from manim import *


class Scene4Scene(Scene):
    def make_title(self, text):
        return Text(text, font_size=40, weight=BOLD).to_edge(UP, buff=0.35)

    def labeled_card(self, label, color, width=3.2, height=2.0):
        rect = RoundedRectangle(
            corner_radius=0.18,
            width=width,
            height=height,
            stroke_color=color,
            stroke_width=4,
            fill_color=color,
            fill_opacity=0.10,
        )
        txt = Text(label, font_size=34, weight=BOLD)
        return VGroup(rect, txt)

    def atom(self, label="", color=BLUE, radius=0.32):
        c = Circle(radius=radius, stroke_color=color, stroke_width=4, fill_color=color, fill_opacity=0.65)
        if label:
            t = Text(label, font_size=26, weight=BOLD, color=WHITE).move_to(c.get_center())
            return VGroup(c, t)
        return VGroup(c)

    def bond(self, start, end):
        return Line(start, end, stroke_color=GRAY_B, stroke_width=8)

    def o2_molecule(self):
        left = self.atom("O", BLUE, 0.45).move_to(LEFT * 0.58)
        right = self.atom("O", BLUE, 0.45).move_to(RIGHT * 0.58)
        b = self.bond(left.get_center(), right.get_center())
        mol = VGroup(b, left, right)
        halos = VGroup(
            Circle(radius=0.56, stroke_color=YELLOW, stroke_width=6).move_to(left.get_center()),
            Circle(radius=0.56, stroke_color=YELLOW, stroke_width=6).move_to(right.get_center()),
        )
        label = Text("O₂", font_size=46, weight=BOLD).next_to(mol, DOWN, buff=0.45)
        one_element = Text("one element", font_size=30, color=YELLOW).next_to(label, DOWN, buff=0.25)
        return VGroup(mol, halos, label, one_element)

    def small_molecule_unit(self):
        a = self.atom("", BLUE, 0.28).move_to(LEFT * 0.45)
        b = self.atom("", GREEN, 0.28).move_to(RIGHT * 0.45)
        line = self.bond(a.get_center(), b.get_center())
        return VGroup(line, a, b)

    def bonded_group(self):
        positions = [LEFT * 0.7, RIGHT * 0.7, UP * 0.55, DOWN * 0.55]
        atoms = VGroup(
            self.atom("", BLUE, 0.28).move_to(positions[0]),
            self.atom("", GREEN, 0.28).move_to(positions[1]),
            self.atom("", ORANGE, 0.28).move_to(positions[2]),
            self.atom("", PURPLE, 0.28).move_to(positions[3]),
        )
        lines = VGroup(
            self.bond(positions[0], positions[2]),
            self.bond(positions[2], positions[1]),
            self.bond(positions[1], positions[3]),
            self.bond(positions[3], positions[0]),
        )
        return VGroup(lines, atoms)

    def repeating_grid(self, rows=4, cols=5, spacing=0.58, radius=0.18):
        grid = VGroup()
        dots = []
        x0 = -(cols - 1) * spacing / 2
        y0 = -(rows - 1) * spacing / 2

        lines = VGroup()
        for r in range(rows):
            for c in range(cols):
                pos = np.array([x0 + c * spacing, y0 + r * spacing, 0])
                if c < cols - 1:
                    end = np.array([x0 + (c + 1) * spacing, y0 + r * spacing, 0])
                    lines.add(Line(pos, end, stroke_color=GRAY_C, stroke_width=3))
                if r < rows - 1:
                    end = np.array([x0 + c * spacing, y0 + (r + 1) * spacing, 0])
                    lines.add(Line(pos, end, stroke_color=GRAY_C, stroke_width=3))

        circles = VGroup()
        for r in range(rows):
            for c in range(cols):
                color = TEAL if (r + c) % 2 == 0 else RED_E
                circ = Circle(
                    radius=radius,
                    stroke_color=color,
                    stroke_width=3,
                    fill_color=color,
                    fill_opacity=0.75,
                ).move_to(np.array([x0 + c * spacing, y0 + r * spacing, 0]))
                circles.add(circ)

        grid.add(lines, circles)
        return grid

    def transition_to(self, old_group, new_group):
        if old_group is not None:
            self.play(FadeOut(old_group, shift=DOWN * 0.2), run_time=0.7)
        self.play(FadeIn(new_group, shift=UP * 0.2), run_time=0.9)
        return new_group

    def construct(self):
        current = None

        title1 = self.make_title("Three common traps")
        cards = VGroup(
            self.labeled_card("molecule", BLUE),
            self.labeled_card("substance", GREEN),
            self.labeled_card("atom", ORANGE),
        ).arrange(RIGHT, buff=0.45).move_to(DOWN * 0.35)
        beat1 = VGroup(title1, cards)
        self.play(Write(title1), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(card, shift=UP * 0.25) for card in cards], lag_ratio=0.22), run_time=1.4)
        self.wait(3.0)
        current = beat1

        title2 = self.make_title("Molecule ≠ always compound")
        panel = RoundedRectangle(
            corner_radius=0.2,
            width=8.8,
            height=3.3,
            stroke_color=WHITE,
            stroke_width=3,
            fill_color=GRAY_E,
            fill_opacity=0.12,
        ).move_to(DOWN * 0.25)
        divider = Line(UP * 1.25, DOWN * 1.25, stroke_color=GRAY_B, stroke_width=3).move_to(panel.get_center())
        left_word = Text("molecule", font_size=40, color=BLUE).move_to(panel.get_center() + LEFT * 2.3)
        right_word = Text("compound", font_size=40, color=GREEN).move_to(panel.get_center() + RIGHT * 2.3)
        not_equal = Text("≠ always", font_size=34, color=YELLOW).move_to(panel.get_center())
        beat2 = VGroup(title2, panel, divider, left_word, right_word, not_equal)
        current = self.transition_to(current, beat2)
        self.wait(5.5)

        title3 = self.make_title("O₂: one element")
        o2 = self.o2_molecule().scale(1.35).move_to(DOWN * 0.2)
        beat3 = VGroup(title3, o2)
        current = self.transition_to(current, beat3)
        self.play(Indicate(o2[1], color=YELLOW, scale_factor=1.08), run_time=1.2)
        self.wait(5.2)

        title4 = self.make_title("Not all substances are molecules")
        split_line = Line(UP * 2.4, DOWN * 2.6, stroke_color=GRAY_B, stroke_width=3)
        left_label = Text("separate molecule unit", font_size=27, color=BLUE).move_to(LEFT * 3.25 + UP * 1.6)
        right_label = Text("repeating structure pattern", font_size=27, color=GREEN).move_to(RIGHT * 3.25 + UP * 1.6)
        left_unit = self.small_molecule_unit().scale(1.55).move_to(LEFT * 3.25 + DOWN * 0.25)
        left_box = SurroundingRectangle(left_unit, buff=0.35, stroke_color=BLUE, stroke_width=3)
        right_grid = self.repeating_grid(rows=4, cols=5, spacing=0.52, radius=0.15).scale(1.15).move_to(RIGHT * 3.25 + DOWN * 0.25)
        beat4 = VGroup(title4, split_line, left_label, right_label, left_unit, left_box, right_grid)
        current = self.transition_to(current, beat4)
        self.wait(6.0)

        title5 = self.make_title("Sodium chloride: repeating structure")
        big_grid = self.repeating_grid(rows=6, cols=8, spacing=0.56, radius=0.18).move_to(DOWN * 0.25)
        grid_label = Text("sodium chloride", font_size=32, color=WHITE).next_to(big_grid, DOWN, buff=0.35)
        beat5 = VGroup(title5, big_grid, grid_label)
        current = self.transition_to(current, beat5)
        self.play(Create(big_grid[0]), run_time=1.0)
        self.play(LaggedStart(*[FadeIn(dot, scale=0.85) for dot in big_grid[1]], lag_ratio=0.02), run_time=1.4)
        self.wait(4.4)

        title6 = self.make_title("Atoms are not always alone")
        single_atom = self.atom("", ORANGE, 0.48).move_to(LEFT * 2.2 + DOWN * 0.15)
        alone_label = Text("atom", font_size=30, color=ORANGE).next_to(single_atom, DOWN, buff=0.3)
        group_atoms = self.bonded_group().scale(1.25).move_to(RIGHT * 1.65 + DOWN * 0.15)
        arrow = Arrow(LEFT * 0.9 + DOWN * 0.15, RIGHT * 0.35 + DOWN * 0.15, buff=0.15, color=WHITE)
        beat6_initial = VGroup(title6, single_atom, alone_label)
        current = self.transition_to(current, beat6_initial)
        self.wait(1.2)
        self.play(FadeIn(arrow), run_time=0.5)
        self.play(FadeOut(single_atom, scale=0.7), FadeOut(alone_label), FadeIn(group_atoms, shift=RIGHT * 0.25), run_time=1.4)
        beat6 = VGroup(title6, arrow, group_atoms)
        current = beat6
        self.wait(4.4)

        title7 = self.make_title("Bonded in molecules or structures")
        molecule_side = self.bonded_group().scale(0.95).move_to(LEFT * 3.15 + DOWN * 0.1)
        molecule_label = Text("molecules", font_size=30, color=BLUE).next_to(molecule_side, DOWN, buff=0.35)
        structure_side = self.repeating_grid(rows=5, cols=6, spacing=0.48, radius=0.14).move_to(RIGHT * 3.05 + DOWN * 0.1)
        structure_label = Text("structures", font_size=30, color=GREEN).next_to(structure_side, DOWN, buff=0.35)
        center_divider = Line(UP * 2.35, DOWN * 2.45, stroke_color=GRAY_B, stroke_width=3)
        beat7 = VGroup(title7, molecule_side, molecule_label, structure_side, structure_label, center_divider)
        current = self.transition_to(current, beat7)
        self.play(
            Indicate(molecule_side, color=YELLOW, scale_factor=1.04),
            Indicate(structure_side, color=YELLOW, scale_factor=1.03),
            run_time=1.5,
        )
        self.wait(5.0)
        self.play(FadeOut(current), run_time=0.8)
        self.wait(0.5)