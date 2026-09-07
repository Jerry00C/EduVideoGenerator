from manim import *


BACKGROUND = "#0f172a"
TEXT_COLOR = "#f8fafc"
MUTED_TEXT = "#cbd5e1"
PANEL_FILL = "#1e293b"
NEUTRAL_ATOM = "#64748b"
OXYGEN_COLOR = "#ef4444"
HYDROGEN_COLOR = "#3b82f6"
BOND_COLOR = "#cbd5e1"


def make_header(text):
    return Text(text, font_size=38, color=TEXT_COLOR, weight="BOLD").to_edge(UP, buff=0.45)


def make_atom(symbol, center, radius=0.45, fill_color=NEUTRAL_ATOM):
    circle = Circle(radius=radius)
    circle.set_fill(fill_color, opacity=1)
    circle.set_stroke(WHITE, width=3)
    circle.move_to(center)

    symbol_text = Text(
        symbol,
        font_size=34 if radius >= 0.42 else 26,
        color=WHITE,
        weight="BOLD",
    ).move_to(center)

    atom = VGroup(circle, symbol_text)
    atom.set_z_index(2)
    return atom


def make_text_label(text, font_size=24):
    return Text(text, font_size=font_size, color=MUTED_TEXT)


def make_note(text):
    box = RoundedRectangle(
        width=3.45,
        height=1.2,
        corner_radius=0.18,
        stroke_color="#fbbf24",
        stroke_width=3,
        fill_color="#422006",
        fill_opacity=0.92,
    )
    label = Text(text, font_size=26, color="#fde68a", weight="BOLD").move_to(box)
    return VGroup(box, label)


def mini_o2(center):
    left = make_atom("O", LEFT * 0.55, radius=0.35, fill_color=OXYGEN_COLOR)
    right = make_atom("O", RIGHT * 0.55, radius=0.35, fill_color=OXYGEN_COLOR)
    bond = Line(left.get_center(), right.get_center(), color=BOND_COLOR, stroke_width=7)
    bond.set_z_index(1)
    group = VGroup(bond, left, right).move_to(center)
    return group


def mini_h2o(center):
    oxygen = make_atom("O", UP * 0.45, radius=0.36, fill_color=OXYGEN_COLOR)
    h_left = make_atom("H", LEFT * 0.75 + DOWN * 0.45, radius=0.27, fill_color=HYDROGEN_COLOR)
    h_right = make_atom("H", RIGHT * 0.75 + DOWN * 0.45, radius=0.27, fill_color=HYDROGEN_COLOR)

    bond1 = Line(oxygen.get_center(), h_left.get_center(), color=BOND_COLOR, stroke_width=6)
    bond2 = Line(oxygen.get_center(), h_right.get_center(), color=BOND_COLOR, stroke_width=6)
    bond1.set_z_index(1)
    bond2.set_z_index(1)

    group = VGroup(bond1, bond2, oxygen, h_left, h_right).move_to(center)
    return group


def comparison_panel(title, subtitle, footer, molecule, center):
    panel = RoundedRectangle(
        width=5.45,
        height=4.25,
        corner_radius=0.22,
        stroke_color="#94a3b8",
        stroke_width=2,
        fill_color=PANEL_FILL,
        fill_opacity=0.85,
    ).move_to(center)

    title_text = Text(title, font_size=34, color=TEXT_COLOR, weight="BOLD").move_to(
        panel.get_top() + DOWN * 0.55
    )
    subtitle_text = Text(subtitle, font_size=24, color=MUTED_TEXT).next_to(
        title_text, DOWN, buff=0.18
    )
    molecule.move_to(center + DOWN * 0.1)
    footer_text = Text(footer, font_size=25, color=TEXT_COLOR, weight="BOLD").move_to(
        panel.get_bottom() + UP * 0.55
    )

    return VGroup(panel, title_text, subtitle_text, molecule, footer_text)


class Scene3Scene(Scene):
    def construct(self):
        self.camera.background_color = BACKGROUND

        header = make_header("Example: oxygen gas")

        o1 = make_atom("O", LEFT * 2.1, radius=0.5, fill_color=NEUTRAL_ATOM)
        o2 = make_atom("O", RIGHT * 2.1, radius=0.5, fill_color=NEUTRAL_ATOM)

        label1 = make_text_label("oxygen atom").next_to(o1, DOWN, buff=0.35)
        label2 = make_text_label("oxygen atom").next_to(o2, DOWN, buff=0.35)

        self.play(
            Write(header),
            FadeIn(o1, shift=UP * 0.2),
            FadeIn(o2, shift=UP * 0.2),
            FadeIn(label1),
            FadeIn(label2),
            run_time=2.2,
        )
        self.wait(5)

        oxygen_molecule_header = make_header("O₂: oxygen molecule")
        self.play(
            Transform(header, oxygen_molecule_header),
            FadeOut(label1),
            FadeOut(label2),
            o1.animate.move_to(LEFT * 0.75),
            o2.animate.move_to(RIGHT * 0.75),
            run_time=2.2,
        )

        o2_bond = Line(o1.get_center(), o2.get_center(), color=BOND_COLOR, stroke_width=8)
        o2_bond.set_z_index(1)
        o2_label = Text("O₂: oxygen molecule", font_size=31, color=TEXT_COLOR, weight="BOLD")
        o2_label.next_to(VGroup(o1, o2), DOWN, buff=0.65)

        self.play(Create(o2_bond), FadeIn(o2_label, shift=UP * 0.15), run_time=1.1)
        self.bring_to_front(o1, o2)
        self.wait(5)

        same_header = make_header("Same element")
        oxygen_tag1 = make_text_label("oxygen", font_size=24).next_to(o1, UP, buff=0.3)
        oxygen_tag2 = make_text_label("oxygen", font_size=24).next_to(o2, UP, buff=0.3)

        self.play(
            Transform(header, same_header),
            o1[0].animate.set_fill(OXYGEN_COLOR, opacity=1),
            o2[0].animate.set_fill(OXYGEN_COLOR, opacity=1),
            FadeIn(oxygen_tag1),
            FadeIn(oxygen_tag2),
            run_time=1.6,
        )
        self.wait(5)

        note = make_note("O₂ is not\na compound")
        note.to_edge(RIGHT, buff=0.65).shift(DOWN * 0.1)

        self.play(FadeIn(note, shift=LEFT * 0.25), run_time=1.0)
        self.wait(5)

        water_header = make_header("Example: water")

        oxygen = make_atom("O", UP * 0.85, radius=0.5, fill_color=NEUTRAL_ATOM)
        h_left = make_atom("H", LEFT * 1.25 + DOWN * 0.75, radius=0.36, fill_color=NEUTRAL_ATOM)
        h_right = make_atom("H", RIGHT * 1.25 + DOWN * 0.75, radius=0.36, fill_color=NEUTRAL_ATOM)
        water_atoms = VGroup(oxygen, h_left, h_right)

        oxygen_scene = VGroup(o1, o2, o2_bond, o2_label, oxygen_tag1, oxygen_tag2, note)

        self.play(
            FadeOut(oxygen_scene, shift=LEFT * 0.25),
            Transform(header, water_header),
            run_time=1.5,
        )
        self.play(FadeIn(water_atoms, shift=UP * 0.2), run_time=1.1)
        self.wait(5)

        h2o_header = make_header("H₂O: water molecule")

        bond_left = Line(oxygen.get_center(), h_left.get_center(), color=BOND_COLOR, stroke_width=8)
        bond_right = Line(oxygen.get_center(), h_right.get_center(), color=BOND_COLOR, stroke_width=8)
        bond_left.set_z_index(1)
        bond_right.set_z_index(1)

        h2o_label = Text("H₂O: water molecule", font_size=31, color=TEXT_COLOR, weight="BOLD")
        h2o_label.next_to(water_atoms, DOWN, buff=0.65)

        self.play(
            Transform(header, h2o_header),
            Create(bond_left),
            Create(bond_right),
            FadeIn(h2o_label, shift=UP * 0.15),
            run_time=2.0,
        )
        self.bring_to_front(oxygen, h_left, h_right)
        self.wait(5)

        different_header = make_header("Different elements")

        oxygen_label = make_text_label("oxygen", font_size=24).next_to(oxygen, UP, buff=0.28)
        hydrogen_label1 = make_text_label("hydrogen", font_size=23).next_to(h_left, DOWN, buff=0.25)
        hydrogen_label2 = make_text_label("hydrogen", font_size=23).next_to(h_right, DOWN, buff=0.25)

        self.play(
            Transform(header, different_header),
            oxygen[0].animate.set_fill(OXYGEN_COLOR, opacity=1),
            h_left[0].animate.set_fill(HYDROGEN_COLOR, opacity=1),
            h_right[0].animate.set_fill(HYDROGEN_COLOR, opacity=1),
            FadeIn(oxygen_label),
            FadeIn(hydrogen_label1),
            FadeIn(hydrogen_label2),
            run_time=1.7,
        )
        self.wait(6)

        final_header = make_header("Molecules can vary")
        both_heading = Text("Both are molecules", font_size=34, color=TEXT_COLOR, weight="BOLD")
        both_heading.move_to(UP * 2.55)

        left_panel = comparison_panel(
            "O₂",
            "oxygen molecule",
            "Same element",
            mini_o2(ORIGIN),
            LEFT * 3.05 + DOWN * 0.25,
        )
        right_panel = comparison_panel(
            "H₂O",
            "water molecule",
            "Different elements",
            mini_h2o(ORIGIN),
            RIGHT * 3.05 + DOWN * 0.25,
        )
        comparison = VGroup(both_heading, left_panel, right_panel)

        water_scene = VGroup(
            water_atoms,
            bond_left,
            bond_right,
            h2o_label,
            oxygen_label,
            hydrogen_label1,
            hydrogen_label2,
        )

        self.play(
            FadeOut(water_scene, shift=DOWN * 0.2),
            Transform(header, final_header),
            run_time=1.4,
        )
        self.play(
            FadeIn(both_heading, shift=DOWN * 0.15),
            LaggedStart(FadeIn(left_panel), FadeIn(right_panel), lag_ratio=0.18),
            run_time=2.4,
        )
        self.wait(9)