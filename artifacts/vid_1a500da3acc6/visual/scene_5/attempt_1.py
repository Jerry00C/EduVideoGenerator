from manim import *


class Scene5Scene(Scene):
    def make_atom(self, center, radius=0.34, color=BLUE, label=None, font_size=22):
        circle = Circle(
            radius=radius,
            stroke_color=color,
            stroke_width=4,
            fill_color=color,
            fill_opacity=0.35,
        ).move_to(center)
        parts = [circle]
        if label:
            parts.append(Text(label, font_size=font_size, color=WHITE).move_to(circle.get_center()))
        return VGroup(*parts)

    def construct(self):
        self.camera.background_color = "#0B1020"

        table_color = "#93C5FD"
        atom_color = "#38BDF8"
        molecule_color = "#A78BFA"
        oxygen_color = "#F87171"
        hydrogen_color = "#60A5FA"
        highlight_color = YELLOW

        title = Text("Atom vs. molecule", font_size=42, color=WHITE).to_edge(UP, buff=0.35)

        outer = RoundedRectangle(
            corner_radius=0.12,
            width=12.2,
            height=5.25,
            stroke_color=table_color,
            stroke_width=3,
        ).move_to(DOWN * 0.15)

        top_y = outer.get_top()[1]
        bottom_y = outer.get_bottom()[1]
        left_x = outer.get_left()[0]
        right_x = outer.get_right()[0]
        header_y = top_y - 0.72

        divider = Line([0, top_y, 0], [0, bottom_y, 0], color=table_color, stroke_width=3)
        header_rule = Line([left_x, header_y, 0], [right_x, header_y, 0], color=table_color, stroke_width=3)

        atom_header = Text("Atom", font_size=34, color=WHITE).move_to([-3.05, top_y - 0.36, 0])
        molecule_header = Text("Molecule", font_size=34, color=WHITE).move_to([3.05, top_y - 0.36, 0])

        self.play(Write(title), run_time=1.0)
        self.play(Create(outer), Create(divider), Create(header_rule), run_time=1.2)
        self.play(FadeIn(atom_header, shift=DOWN * 0.15), FadeIn(molecule_header, shift=DOWN * 0.15), run_time=0.9)
        self.wait(1.2)

        atom_def = Text("Atom: one unit", font_size=30, color=WHITE).move_to([-3.05, 1.05, 0])
        atom_icon = self.make_atom([-3.05, 0.1, 0], radius=0.47, color=atom_color)

        self.play(FadeIn(atom_icon, scale=0.85), Write(atom_def), run_time=1.5)
        self.play(Circumscribe(atom_icon, color=highlight_color, run_time=1.0))
        self.wait(1.4)

        mol_def = Text("Molecule: bonded atoms", font_size=28, color=WHITE).move_to([3.05, 1.05, 0])
        mol_left = self.make_atom([2.65, 0.22, 0], radius=0.34, color=molecule_color)
        mol_right = self.make_atom([3.45, 0.22, 0], radius=0.34, color=molecule_color)
        mol_bond = Line(mol_left.get_center(), mol_right.get_center(), color=WHITE, stroke_width=7)
        mol_icon = VGroup(mol_bond, mol_left, mol_right)

        self.play(FadeIn(mol_icon, scale=0.85), Write(mol_def), run_time=1.5)
        self.play(Circumscribe(mol_icon, color=highlight_color, run_time=1.0))
        self.wait(1.4)

        o2_label = Text("O2: same element", font_size=26, color=WHITE).move_to([2.0, -0.73, 0])
        o2_left = self.make_atom([4.35, -0.73, 0], radius=0.25, color=oxygen_color, label="O", font_size=18)
        o2_right = self.make_atom([4.95, -0.73, 0], radius=0.25, color=oxygen_color, label="O", font_size=18)
        o2_bond = Line(o2_left.get_center(), o2_right.get_center(), color=WHITE, stroke_width=5)
        o2_ring_left = Circle(radius=0.32, color=highlight_color, stroke_width=4).move_to(o2_left.get_center())
        o2_ring_right = Circle(radius=0.32, color=highlight_color, stroke_width=4).move_to(o2_right.get_center())
        o2_group = VGroup(o2_bond, o2_left, o2_right)

        self.play(Write(o2_label), FadeIn(o2_group, scale=0.9), run_time=1.4)
        self.play(Create(o2_ring_left), Create(o2_ring_right), run_time=0.8)
        self.wait(1.6)

        h2o_label = Text("H2O: different elements", font_size=25, color=WHITE).move_to([2.15, -1.78, 0])
        o_atom = self.make_atom([4.82, -1.78, 0], radius=0.25, color=oxygen_color, label="O", font_size=18)
        h_atom_1 = self.make_atom([4.35, -1.43, 0], radius=0.21, color=hydrogen_color, label="H", font_size=16)
        h_atom_2 = self.make_atom([4.35, -2.13, 0], radius=0.21, color=hydrogen_color, label="H", font_size=16)
        h_bond_1 = Line(o_atom.get_center(), h_atom_1.get_center(), color=WHITE, stroke_width=5)
        h_bond_2 = Line(o_atom.get_center(), h_atom_2.get_center(), color=WHITE, stroke_width=5)
        h2o_group = VGroup(h_bond_1, h_bond_2, h_atom_1, h_atom_2, o_atom)

        h_ring_1 = Circle(radius=0.28, color=hydrogen_color, stroke_width=4).move_to(h_atom_1.get_center())
        h_ring_2 = Circle(radius=0.28, color=hydrogen_color, stroke_width=4).move_to(h_atom_2.get_center())
        o_ring = Circle(radius=0.33, color=oxygen_color, stroke_width=4).move_to(o_atom.get_center())

        self.play(Write(h2o_label), FadeIn(h2o_group, scale=0.9), run_time=1.5)
        self.play(Create(h_ring_1), Create(h_ring_2), Create(o_ring), run_time=0.9)
        self.wait(1.6)

        summary_text = Text("Atom: one. Molecule: bonded group.", font_size=31, color=WHITE)
        summary_box = RoundedRectangle(
            corner_radius=0.15,
            width=7.9,
            height=0.62,
            stroke_color=highlight_color,
            stroke_width=3,
            fill_color="#1E293B",
            fill_opacity=0.85,
        ).move_to([0, -3.43, 0])
        summary_text.move_to(summary_box.get_center())
        summary = VGroup(summary_box, summary_text)

        self.play(FadeIn(summary, shift=UP * 0.15), run_time=1.1)
        self.play(Circumscribe(VGroup(outer, divider, header_rule), color=highlight_color, run_time=1.3))
        self.wait(3.0)