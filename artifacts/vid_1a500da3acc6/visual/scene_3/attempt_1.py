from manim import *

OXYGEN_COLOR = "#D94B4B"
HYDROGEN_COLOR = "#4A90E2"
NEUTRAL_COLOR = "#6B7280"
BOND_COLOR = "#BFC7D5"


def make_atom(symbol, color, position, radius=0.55, symbol_size=34):
    circle = Circle(radius=radius)
    circle.set_fill(color, opacity=0.9)
    circle.set_stroke(WHITE, width=2)
    circle.move_to(position)
    label = Text(symbol, font_size=symbol_size, weight=BOLD, color=WHITE)
    label.move_to(circle.get_center())
    atom = VGroup(circle, label)
    atom.set_z_index(2)
    return atom


def make_bond(atom_a, atom_b, stroke_width=8):
    line = Line(atom_a[0].get_center(), atom_b[0].get_center())
    line.set_stroke(BOND_COLOR, width=stroke_width)
    line.set_z_index(0)
    return line


def top_text(text):
    return Text(text, font_size=36, weight=BOLD, color=WHITE).to_edge(UP)


class Scene3Scene(Scene):
    def construct(self):
        self.camera.background_color = "#111827"

        # vis_3_1: oxygen gas, separated atoms
        header = top_text("Example: oxygen gas")

        o1 = make_atom("O", OXYGEN_COLOR, LEFT * 2.1 + UP * 0.15)
        o2 = make_atom("O", OXYGEN_COLOR, RIGHT * 2.1 + UP * 0.15)

        o1_label = Text("oxygen atom", font_size=24, color=WHITE).next_to(o1, DOWN, buff=0.28)
        o2_label = Text("oxygen atom", font_size=24, color=WHITE).next_to(o2, DOWN, buff=0.28)

        self.play(FadeIn(header, shift=DOWN * 0.2), run_time=0.8)
        self.play(
            LaggedStart(
                FadeIn(o1, shift=UP * 0.2),
                FadeIn(o2, shift=UP * 0.2),
                lag_ratio=0.25,
            ),
            run_time=0.8,
        )
        self.play(Write(o1_label), Write(o2_label), run_time=0.5)
        self.wait(5)

        # vis_3_2: bond oxygen atoms and label O2
        header2 = top_text("O2: oxygen molecule")
        self.play(
            FadeTransform(header, header2),
            FadeOut(o1_label),
            FadeOut(o2_label),
            run_time=0.5,
        )
        header = header2

        self.play(
            o1.animate.move_to(LEFT * 0.62 + UP * 0.15),
            o2.animate.move_to(RIGHT * 0.62 + UP * 0.15),
            run_time=0.9,
        )

        o2_bond = make_bond(o1, o2)
        o2_label = Text("O2: oxygen molecule", font_size=30, color=WHITE)
        o2_label.next_to(VGroup(o1, o2), DOWN, buff=0.55)

        self.play(Create(o2_bond), FadeIn(o2_label, shift=DOWN * 0.15), run_time=0.8)
        self.wait(5)

        # vis_3_3: same element
        header3 = top_text("Same element")
        same_lab1 = Text("oxygen", font_size=24, color=OXYGEN_COLOR).next_to(o1, UP, buff=0.18)
        same_lab2 = Text("oxygen", font_size=24, color=OXYGEN_COLOR).next_to(o2, UP, buff=0.18)

        self.play(FadeTransform(header, header3), run_time=0.5)
        header = header3
        self.play(
            o1[0].animate.set_fill(OXYGEN_COLOR, opacity=0.95),
            o2[0].animate.set_fill(OXYGEN_COLOR, opacity=0.95),
            run_time=0.5,
        )
        self.play(
            Write(same_lab1),
            Write(same_lab2),
            Indicate(VGroup(o1, o2), color=OXYGEN_COLOR, scale_factor=1.08),
            run_time=0.8,
        )
        self.wait(5)

        # vis_3_4: O2 note
        note = Text("O2 is not a compound", font_size=28, color=YELLOW)
        note.next_to(VGroup(o1, o2, o2_label), RIGHT, buff=0.75)
        note_box = SurroundingRectangle(note, buff=0.25, corner_radius=0.12, color=YELLOW)
        self.play(FadeIn(note_box), Write(note), run_time=0.8)
        self.wait(6)

        # vis_3_5: transition to water atoms
        old_group = VGroup(header, o1, o2, o2_bond, o2_label, same_lab1, same_lab2, note, note_box)
        header5 = top_text("Example: water")

        w_o = make_atom("O", NEUTRAL_COLOR, DOWN * 0.35, radius=0.55, symbol_size=34)
        w_h1 = make_atom("H", NEUTRAL_COLOR, LEFT * 1.25 + UP * 0.75, radius=0.43, symbol_size=28)
        w_h2 = make_atom("H", NEUTRAL_COLOR, RIGHT * 1.25 + UP * 0.75, radius=0.43, symbol_size=28)

        self.play(FadeOut(old_group), FadeIn(header5, shift=DOWN * 0.2), run_time=0.8)
        header = header5
        self.play(
            LaggedStart(
                FadeIn(w_o, shift=UP * 0.15),
                FadeIn(w_h1, shift=UP * 0.15),
                FadeIn(w_h2, shift=UP * 0.15),
                lag_ratio=0.18,
            ),
            run_time=0.8,
        )
        self.wait(6)

        # vis_3_6: bond H2O and label
        header6 = top_text("H2O: water molecule")
        self.play(FadeTransform(header, header6), run_time=0.5)
        header = header6

        bond_oh1 = make_bond(w_o, w_h1, stroke_width=7)
        bond_oh2 = make_bond(w_o, w_h2, stroke_width=7)
        h2o_label = Text("H2O: water molecule", font_size=30, color=WHITE)
        h2o_label.next_to(VGroup(w_o, w_h1, w_h2), DOWN, buff=0.6)

        self.play(Create(bond_oh1), Create(bond_oh2), run_time=0.8)
        self.play(FadeIn(h2o_label, shift=DOWN * 0.15), run_time=0.6)
        self.wait(6)

        # vis_3_7: different elements
        header7 = top_text("Different elements")
        h1_text = Text("hydrogen", font_size=22, color=HYDROGEN_COLOR).next_to(w_h1, UP, buff=0.18)
        h2_text = Text("hydrogen", font_size=22, color=HYDROGEN_COLOR).next_to(w_h2, UP, buff=0.18)
        o_text = Text("oxygen", font_size=22, color=OXYGEN_COLOR).next_to(w_o, RIGHT, buff=0.35)

        self.play(FadeTransform(header, header7), run_time=0.5)
        header = header7
        self.play(
            w_h1[0].animate.set_fill(HYDROGEN_COLOR, opacity=0.95),
            w_h2[0].animate.set_fill(HYDROGEN_COLOR, opacity=0.95),
            w_o[0].animate.set_fill(OXYGEN_COLOR, opacity=0.95),
            run_time=0.5,
        )
        self.play(
            Write(h1_text),
            Write(h2_text),
            Write(o_text),
            Indicate(VGroup(w_h1, w_h2), color=HYDROGEN_COLOR, scale_factor=1.08),
            Indicate(w_o, color=OXYGEN_COLOR, scale_factor=1.08),
            run_time=0.8,
        )
        self.wait(6)

        # vis_3_8: comparison table, O2 and H2O side by side
        current_water = VGroup(
            header, w_o, w_h1, w_h2, bond_oh1, bond_oh2, h2o_label, h1_text, h2_text, o_text
        )

        final_header = top_text("Molecules can vary")
        shared = Text("Both are molecules", font_size=30, color=WHITE).next_to(final_header, DOWN, buff=0.25)

        left_card = RoundedRectangle(width=5.25, height=3.55, corner_radius=0.18)
        left_card.set_stroke(BLUE_B, width=2)
        left_card.move_to(LEFT * 3 + DOWN * 0.25)

        right_card = RoundedRectangle(width=5.25, height=3.55, corner_radius=0.18)
        right_card.set_stroke(BLUE_B, width=2)
        right_card.move_to(RIGHT * 3 + DOWN * 0.25)

        left_title = Text("O2", font_size=30, weight=BOLD, color=WHITE).next_to(left_card.get_top(), DOWN, buff=0.28)
        right_title = Text("H2O", font_size=30, weight=BOLD, color=WHITE).next_to(right_card.get_top(), DOWN, buff=0.28)

        lo1 = make_atom("O", OXYGEN_COLOR, left_card.get_center() + LEFT * 0.45 + UP * 0.25, radius=0.36, symbol_size=24)
        lo2 = make_atom("O", OXYGEN_COLOR, left_card.get_center() + RIGHT * 0.45 + UP * 0.25, radius=0.36, symbol_size=24)
        lbond = make_bond(lo1, lo2, stroke_width=6)
        left_note = Text("same element", font_size=24, color=OXYGEN_COLOR).next_to(VGroup(lo1, lo2), DOWN, buff=0.48)

        ro = make_atom("O", OXYGEN_COLOR, right_card.get_center() + DOWN * 0.05, radius=0.36, symbol_size=24)
        rh1 = make_atom("H", HYDROGEN_COLOR, right_card.get_center() + LEFT * 0.78 + UP * 0.65, radius=0.3, symbol_size=21)
        rh2 = make_atom("H", HYDROGEN_COLOR, right_card.get_center() + RIGHT * 0.78 + UP * 0.65, radius=0.3, symbol_size=21)
        rbond1 = make_bond(ro, rh1, stroke_width=6)
        rbond2 = make_bond(ro, rh2, stroke_width=6)
        right_note = Text("different elements", font_size=24, color=WHITE).next_to(VGroup(ro, rh1, rh2), DOWN, buff=0.48)

        comparison = VGroup(
            final_header,
            shared,
            left_card,
            right_card,
            left_title,
            right_title,
            lbond,
            lo1,
            lo2,
            left_note,
            rbond1,
            rbond2,
            ro,
            rh1,
            rh2,
            right_note,
        )

        self.play(FadeOut(current_water), run_time=0.8)
        self.play(
            LaggedStart(
                FadeIn(final_header, shift=DOWN * 0.15),
                FadeIn(shared, shift=DOWN * 0.1),
                FadeIn(VGroup(left_card, right_card)),
                FadeIn(VGroup(left_title, right_title)),
                FadeIn(VGroup(lbond, lo1, lo2, left_note)),
                FadeIn(VGroup(rbond1, rbond2, ro, rh1, rh2, right_note)),
                lag_ratio=0.18,
            ),
            run_time=1.4,
        )
        self.wait(8)