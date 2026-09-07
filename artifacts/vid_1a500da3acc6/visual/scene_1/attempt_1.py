from manim import *


class Scene1Scene(Scene):
    def construct(self):
        self.camera.background_color = "#10151F"

        def make_atom(color="#58A6FF", radius=0.62):
            body = Circle(radius=radius, stroke_width=3)
            body.set_fill(color, opacity=1)
            body.set_stroke(WHITE, opacity=0.35)

            highlight = Circle(radius=radius * 0.18, stroke_width=0)
            highlight.set_fill(WHITE, opacity=0.45)
            highlight.move_to(UL * radius * 0.35)

            rim = Circle(radius=radius, stroke_width=4)
            rim.set_stroke(WHITE, opacity=0.18)

            return VGroup(body, highlight, rim)

        atom_center = UP * 0.25
        label_center = DOWN * 1.75

        title = Text("Atom vs. molecule", font_size=54, weight="BOLD", color=WHITE)
        self.play(Write(title), run_time=1.5)
        self.wait(2.0)

        top_title = title.copy().scale(0.72).to_edge(UP, buff=0.45)
        atom = make_atom("#58A6FF").move_to(atom_center)
        atom.set_z_index(3)

        self.play(Transform(title, top_title), run_time=1.2)
        self.play(FadeIn(atom, scale=0.8), run_time=1.3)
        self.wait(3.0)

        diagram_box = RoundedRectangle(
            width=8.5,
            height=4.7,
            corner_radius=0.22,
            stroke_width=3,
            color="#7FB3D5",
        )
        diagram_box.move_to(DOWN * 0.55)
        diagram_box.set_fill("#162235", opacity=0.35)
        diagram_box.set_z_index(0)

        atom_label = Text(
            "Atom: one unit of an element",
            font_size=34,
            color=WHITE,
            weight="MEDIUM",
        ).move_to(label_center)
        atom_label.set_z_index(3)

        highlight_ring = Circle(radius=0.84, color=YELLOW, stroke_width=6)
        highlight_ring.move_to(atom_center)
        highlight_ring.set_z_index(2)

        self.play(FadeIn(diagram_box), Write(atom_label), run_time=2.0)
        self.play(Create(highlight_ring), run_time=0.8)
        self.play(Indicate(highlight_ring, color=YELLOW, scale_factor=1.12), run_time=1.1)
        self.wait(6.0)

        hydrogen_label = Text(
            "One hydrogen atom",
            font_size=38,
            color=WHITE,
            weight="MEDIUM",
        ).move_to(label_center)
        hydrogen_label.set_z_index(3)

        self.play(Transform(atom_label, hydrogen_label), run_time=1.4)
        self.play(
            Indicate(atom, color=YELLOW, scale_factor=1.08),
            Indicate(highlight_ring, color=YELLOW, scale_factor=1.08),
            run_time=1.1,
        )
        self.wait(6.5)

        oxygen_atom = make_atom("#FF6B6B").move_to(atom_center)
        oxygen_atom.set_z_index(3)

        oxygen_label = Text(
            "One oxygen atom",
            font_size=38,
            color=WHITE,
            weight="MEDIUM",
        ).move_to(label_center)
        oxygen_label.set_z_index(3)

        self.play(
            Transform(atom, oxygen_atom),
            Transform(atom_label, oxygen_label),
            highlight_ring.animate.set_stroke(YELLOW, opacity=1),
            run_time=1.6,
        )
        self.play(
            Indicate(atom, color=YELLOW, scale_factor=1.08),
            Indicate(highlight_ring, color=YELLOW, scale_factor=1.08),
            run_time=1.1,
        )
        self.wait(6.5)

        summary = Text(
            "Atom = one basic unit",
            font_size=34,
            color=WHITE,
            weight="BOLD",
        )
        summary.next_to(atom, RIGHT, buff=1.15)
        summary.set_z_index(5)

        summary_box = RoundedRectangle(
            width=summary.width + 0.55,
            height=summary.height + 0.35,
            corner_radius=0.18,
            stroke_width=3,
            color=YELLOW,
        )
        summary_box.move_to(summary)
        summary_box.set_fill("#2B2A12", opacity=0.8)
        summary_box.set_z_index(4)

        connector = Line(
            atom.get_right() + RIGHT * 0.18,
            summary_box.get_left() + LEFT * 0.06,
            color=YELLOW,
            stroke_width=4,
        )
        connector.set_z_index(3)

        self.play(
            title.animate.set_opacity(0.25),
            atom_label.animate.set_opacity(0.25),
            diagram_box.animate.set_opacity(0.25),
            Create(connector),
            FadeIn(summary_box),
            Write(summary),
            run_time=2.0,
        )
        self.play(Indicate(summary_box, color=YELLOW, scale_factor=1.04), run_time=1.0)
        self.wait(7.9)