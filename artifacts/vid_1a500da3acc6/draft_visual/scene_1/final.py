from manim import *


class Scene1Scene(Scene):
    def make_atom(self, color=BLUE, radius=0.8):
        body = Circle(
            radius=radius,
            stroke_color=WHITE,
            stroke_width=3,
            fill_color=color,
            fill_opacity=0.9,
        )
        shine = Circle(
            radius=radius * 0.18,
            stroke_width=0,
            fill_color=WHITE,
            fill_opacity=0.35,
        ).move_to(body.get_center() + UP * radius * 0.35 + LEFT * radius * 0.28)
        return VGroup(body, shine)

    def make_label_box(self, text, font_size=34):
        label = Text(text, font_size=font_size, color=WHITE)
        box = RoundedRectangle(
            width=label.width + 0.65,
            height=label.height + 0.38,
            corner_radius=0.14,
            stroke_color=WHITE,
            stroke_width=2,
            fill_color=BLACK,
            fill_opacity=0.45,
        ).move_to(label)
        return VGroup(box, label)

    def construct(self):
        self.camera.background_color = "#10131A"

        title = Text("Atom vs. molecule", font_size=56, color=WHITE)
        self.play(Write(title), run_time=1.4)
        self.wait(1.8)

        atom = self.make_atom(BLUE, radius=0.82).move_to(ORIGIN + UP * 0.15)
        small_atom_label = Text("atom", font_size=30, color=WHITE).next_to(atom, DOWN, buff=0.35)

        self.play(
            title.animate.to_edge(UP, buff=0.45).scale(0.78),
            FadeIn(atom, scale=0.7),
            Write(small_atom_label),
            run_time=2.2,
        )
        self.wait(4.2)

        identity_group = self.make_label_box("Atom: one unit of an element", font_size=34)
        identity_group.next_to(atom, DOWN, buff=0.7)

        highlight = Circle(
            radius=1.0,
            stroke_color=YELLOW,
            stroke_width=6,
            fill_opacity=0,
        ).move_to(atom)

        self.play(
            FadeOut(small_atom_label),
            FadeIn(identity_group, shift=UP * 0.15),
            Create(highlight),
            run_time=1.8,
        )
        self.play(Indicate(atom, color=YELLOW, scale_factor=1.08), run_time=1.5)
        self.wait(5.6)

        hydrogen_group = self.make_label_box("One hydrogen atom", font_size=36)
        hydrogen_group.next_to(atom, DOWN, buff=0.7)

        self.play(
            Transform(identity_group, hydrogen_group),
            highlight.animate.set_stroke(YELLOW, width=7),
            run_time=1.7,
        )
        self.play(Indicate(atom, color=YELLOW, scale_factor=1.07), run_time=1.2)
        self.wait(6.0)

        oxygen_atom = self.make_atom(RED_E, radius=0.86).move_to(atom.get_center())
        oxygen_highlight = Circle(
            radius=1.04,
            stroke_color=YELLOW,
            stroke_width=7,
            fill_opacity=0,
        ).move_to(atom)

        oxygen_group = self.make_label_box("One oxygen atom", font_size=36)
        oxygen_group.next_to(atom, DOWN, buff=0.68)

        self.play(
            Transform(atom, oxygen_atom),
            Transform(highlight, oxygen_highlight),
            Transform(identity_group, oxygen_group),
            run_time=2.0,
        )
        self.play(Indicate(atom, color=YELLOW, scale_factor=1.07), run_time=1.2)
        self.wait(6.0)

        summary_group = self.make_label_box("Atom = one basic unit", font_size=34)
        summary_group.set_color(YELLOW)
        summary_group[0].set_stroke(YELLOW, width=2)
        summary_group[0].set_fill(BLACK, opacity=0.55)

        left_shift = LEFT * 1.45
        self.play(
            atom.animate.shift(left_shift),
            highlight.animate.shift(left_shift),
            identity_group.animate.shift(left_shift),
            run_time=1.5,
        )

        summary_group.next_to(atom, RIGHT, buff=0.75)
        self.play(
            title.animate.set_opacity(0.25),
            identity_group.animate.set_opacity(0.25),
            FadeIn(summary_group, shift=LEFT * 0.2),
            run_time=1.8,
        )
        self.play(Indicate(summary_group, color=YELLOW, scale_factor=1.03), run_time=1.2)
        self.wait(8.5)