from manim import *


class Scene4Scene(Scene):
    def make_title(self, text):
        return Text(text, font_size=34, color=WHITE).to_edge(UP, buff=0.35)

    def make_card(self, label, width=3.0, height=1.35, color=BLUE):
        box = RoundedRectangle(
            width=width,
            height=height,
            corner_radius=0.18,
            stroke_color=color,
            stroke_width=4,
            fill_color=color,
            fill_opacity=0.18,
        )
        text = Text(label, font_size=30, color=WHITE)
        text.move_to(box.get_center())
        return VGroup(box, text)

    def atom(self, label="", color=BLUE, radius=0.32):
        circle = Circle(radius=radius, stroke_color=WHITE, stroke_width=3)
        circle.set_fill(color, opacity=0.88)
        if label:
            text = Text(label, font_size=25, color=WHITE).move_to(circle)
            return VGroup(circle, text)
        return VGroup(circle)

    def bonded_cluster(self, coords, edges, colors=None, labels=None, radius=0.32):
        if colors is None:
            colors = [BLUE] * len(coords)
        if labels is None:
            labels = [""] * len(coords)

        atoms = VGroup()
        points = []
        for (x, y), color, label in zip(coords, colors, labels):
            a = self.atom(label, color=color, radius=radius)
            a.move_to(x * RIGHT + y * UP)
            atoms.add(a)
            points.append(a.get_center())

        bonds = VGroup()
        for i, j in edges:
            bonds.add(Line(points[i], points[j], color=GREY_B, stroke_width=7))

        return VGroup(bonds, atoms)

    def repeating_grid(self, rows=5, cols=7, spacing=0.55, radius=0.19):
        grid = VGroup()
        colors = [TEAL_E, ORANGE]
        for r in range(rows):
            for c in range(cols):
                dot = Circle(radius=radius, stroke_color=WHITE, stroke_width=2)
                dot.set_fill(colors[(r + c) % 2], opacity=0.9)
                dot.move_to(
                    (c - (cols - 1) / 2) * spacing * RIGHT
                    + ((rows - 1) / 2 - r) * spacing * UP
                )
                grid.add(dot)
        return grid

    def clear_scene(self):
        if self.mobjects:
            self.play(FadeOut(Group(*self.mobjects)), run_time=0.5)
            self.wait(0.1)

    def construct(self):
        self.camera.background_color = "#101820"

        title = self.make_title("Three common traps")
        cards = VGroup(
            self.make_card("molecule", color=BLUE),
            self.make_card("substance", color=GREEN),
            self.make_card("atom", color=PURPLE),
        ).arrange(RIGHT, buff=0.55).move_to(ORIGIN)
        self.play(FadeIn(title, shift=DOWN * 0.2), run_time=0.8)
        self.play(
            LaggedStart(
                *[FadeIn(card, shift=UP * 0.25) for card in cards],
                lag_ratio=0.18,
            ),
            run_time=1.0,
        )
        self.wait(4.0)
        self.clear_scene()

        title = self.make_title("Molecule ≠ always compound")
        left = self.make_card("molecule", width=3.2, color=BLUE).shift(LEFT * 2.4)
        right = self.make_card("compound", width=3.2, color=ORANGE).shift(RIGHT * 2.4)
        neq = Text("≠", font_size=72, color=YELLOW)
        self.play(FadeIn(title, shift=DOWN * 0.2), run_time=0.7)
        self.play(FadeIn(left), FadeIn(right), Write(neq), run_time=1.1)
        self.wait(4.7)
        self.clear_scene()

        title = self.make_title("O2: one element")
        o1 = self.atom("O", color=BLUE_D, radius=0.42).shift(LEFT * 0.52)
        o2 = self.atom("O", color=BLUE_D, radius=0.42).shift(RIGHT * 0.52)
        bond = Line(o1.get_center(), o2.get_center(), color=GREY_B, stroke_width=8)
        molecule = VGroup(bond, o1, o2).move_to(UP * 0.1)
        highlights = VGroup(
            Circle(radius=0.49, color=YELLOW, stroke_width=5).move_to(o1[0].get_center()),
            Circle(radius=0.49, color=YELLOW, stroke_width=5).move_to(o2[0].get_center()),
        )
        label = Text("one element", font_size=30, color=YELLOW).next_to(molecule, DOWN, buff=0.55)
        self.play(FadeIn(title, shift=DOWN * 0.2), run_time=0.7)
        self.play(Create(bond), FadeIn(o1), FadeIn(o2), run_time=1.1)
        self.play(Create(highlights), FadeIn(label, shift=UP * 0.15), run_time=1.0)
        self.wait(4.8)
        self.clear_scene()

        title = self.make_title("Not all substances are molecules")
        divider = Line(UP * 2.25, DOWN * 2.45, color=GREY_B, stroke_width=3)
        left_panel = RoundedRectangle(
            width=5.25,
            height=4.45,
            corner_radius=0.14,
            stroke_color=BLUE,
            stroke_width=3,
            fill_color=BLUE_E,
            fill_opacity=0.1,
        ).move_to(LEFT * 3.2 + DOWN * 0.15)
        right_panel = RoundedRectangle(
            width=5.25,
            height=4.45,
            corner_radius=0.14,
            stroke_color=GREEN,
            stroke_width=3,
            fill_color=GREEN_E,
            fill_opacity=0.1,
        ).move_to(RIGHT * 3.2 + DOWN * 0.15)

        unit = self.bonded_cluster(
            coords=[(-0.55, 0), (0.55, 0), (0, 0.72)],
            edges=[(0, 1), (0, 2), (1, 2)],
            colors=[BLUE, BLUE, BLUE],
            radius=0.3,
        ).move_to(LEFT * 3.2 + UP * 0.25)
        unit_label = Text("separate molecule unit", font_size=23, color=WHITE).next_to(
            left_panel, DOWN, buff=0.12
        )

        pattern = self.repeating_grid(rows=4, cols=6, spacing=0.48, radius=0.17).move_to(
            RIGHT * 3.2 + UP * 0.25
        )
        pattern_label = Text("repeating structure pattern", font_size=23, color=WHITE).next_to(
            right_panel, DOWN, buff=0.12
        )

        self.play(FadeIn(title, shift=DOWN * 0.2), run_time=0.7)
        self.play(FadeIn(left_panel), FadeIn(right_panel), Create(divider), run_time=0.8)
        self.play(FadeIn(unit), FadeIn(pattern), FadeIn(unit_label), FadeIn(pattern_label), run_time=1.2)
        self.wait(4.7)
        self.clear_scene()

        title = self.make_title("Sodium chloride: repeating structure")
        grid_frame = RoundedRectangle(
            width=5.3,
            height=3.7,
            corner_radius=0.12,
            stroke_color=GREY_B,
            stroke_width=3,
            fill_color=WHITE,
            fill_opacity=0.04,
        ).move_to(DOWN * 0.15)
        big_grid = self.repeating_grid(rows=6, cols=9, spacing=0.48, radius=0.17).move_to(DOWN * 0.15)
        self.play(FadeIn(title, shift=DOWN * 0.2), run_time=0.7)
        self.play(FadeIn(grid_frame), LaggedStart(*[FadeIn(dot) for dot in big_grid], lag_ratio=0.015), run_time=1.5)
        self.wait(4.9)
        self.clear_scene()

        title = self.make_title("Atoms are not always alone")
        single = self.atom("", color=PURPLE, radius=0.55).move_to(ORIGIN)
        single_label = Text("atom", font_size=26, color=WHITE).next_to(single, DOWN, buff=0.35)

        group = self.bonded_cluster(
            coords=[(-0.8, 0), (0, 0.55), (0.8, 0), (0, -0.62)],
            edges=[(0, 1), (1, 2), (0, 3), (2, 3)],
            colors=[PURPLE, BLUE, GREEN, ORANGE],
            radius=0.34,
        ).move_to(ORIGIN)
        self.play(FadeIn(title, shift=DOWN * 0.2), run_time=0.7)
        self.play(FadeIn(single), FadeIn(single_label), run_time=0.8)
        self.play(
            FadeOut(single, scale=0.85),
            FadeOut(single_label),
            FadeIn(group, scale=1.08),
            run_time=1.3,
        )
        self.wait(4.4)
        self.clear_scene()

        title = self.make_title("Bonded in molecules or structures")
        divider = Line(UP * 2.25, DOWN * 2.35, color=GREY_B, stroke_width=3)
        molecule = self.bonded_cluster(
            coords=[(-0.65, 0), (0.15, 0.58), (0.75, -0.12)],
            edges=[(0, 1), (1, 2)],
            colors=[BLUE, GREEN, BLUE],
            radius=0.33,
        ).move_to(LEFT * 3.15 + UP * 0.15)
        molecule_label = Text("molecule", font_size=25, color=WHITE).next_to(molecule, DOWN, buff=0.45)

        structure = self.repeating_grid(rows=5, cols=6, spacing=0.45, radius=0.16).move_to(
            RIGHT * 3.15 + UP * 0.15
        )
        structure_label = Text("larger structure", font_size=25, color=WHITE).next_to(
            structure, DOWN, buff=0.45
        )

        self.play(FadeIn(title, shift=DOWN * 0.2), run_time=0.7)
        self.play(Create(divider), run_time=0.5)
        self.play(FadeIn(molecule, shift=RIGHT * 0.15), FadeIn(molecule_label), run_time=1.0)
        self.play(FadeIn(structure, shift=LEFT * 0.15), FadeIn(structure_label), run_time=1.0)
        self.wait(4.5)