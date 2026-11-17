"""Properties of the contrast repair (color.readable_pair and its callers) for any
colors, not only for today's palette: a kanso.nvim update can bring new ones.

`nix flake check` sets HYPOTHESIS_PROFILE=ci: a fixed seed and no example database.
"""

import os
import unittest
from pathlib import Path

from hypothesis import assume, given, settings
from hypothesis import strategies as st

from kanso_jetbrains import editor_scheme, intellij
from kanso_jetbrains.color import contrast, readable_pair
from kanso_jetbrains.variants import load_variants

settings.register_profile("ci", database=None, derandomize=True)
settings.load_profile(os.environ.get("HYPOTHESIS_PROFILE", "default"))

VARIANTS = load_variants(Path(__file__).resolve().parent.parent / "palette" / "kanso.json")

opaque_colors = st.integers(0, 0xFFFFFF).map(lambda n: f"#{n:06X}")
translucent_colors = st.tuples(opaque_colors, st.integers(0, 0xFF)).map(lambda c: f"{c[0]}{c[1]:02X}")
any_colors = opaque_colors | translucent_colors
minimums = st.sampled_from([editor_scheme.MIN_CODE_CONTRAST, 4.5, 7.0])


class ReadablePairTest(unittest.TestCase):
    @given(opaque_colors, opaque_colors, opaque_colors, opaque_colors, minimums)
    def test_result_reaches_the_minimum(self, fg, bg, light, dark, minimum):
        assume(contrast(light, dark) >= minimum)
        fixed_fg, fixed_bg = readable_pair(fg, bg, light, dark, minimum)
        self.assertGreaterEqual(contrast(fixed_fg, fixed_bg), minimum)

    @given(opaque_colors, opaque_colors, opaque_colors, opaque_colors, minimums)
    def test_readable_pairs_stay_unchanged(self, fg, bg, light, dark, minimum):
        assume(contrast(fg, bg) >= minimum)
        self.assertEqual(readable_pair(fg, bg, light, dark, minimum), (fg, bg))

    @given(opaque_colors, opaque_colors, opaque_colors, opaque_colors, minimums)
    def test_background_moves_only_when_no_foreground_suffices(self, fg, bg, light, dark, minimum):
        assume(contrast(light, dark) >= minimum)
        assume(max(contrast(light, bg), contrast(dark, bg)) >= minimum)
        self.assertEqual(readable_pair(fg, bg, light, dark, minimum)[1], bg)

    @given(opaque_colors, opaque_colors, opaque_colors, opaque_colors, minimums)
    def test_too_close_extremes_are_an_error(self, fg, bg, light, dark, minimum):
        assume(contrast(fg, bg) < minimum and contrast(light, dark) < minimum)
        with self.assertRaises(ValueError):
            readable_pair(fg, bg, light, dark, minimum)


class EditorReadableTest(unittest.TestCase):
    @given(st.sampled_from(VARIANTS), any_colors, st.none() | any_colors)
    def test_any_attribute_becomes_readable(self, v, fg, bg):
        """Any foreground on the editor background or on its own, possibly
        translucent background ends at 3:1 or more as the IDE paints it, without
        an error: Kansō's lightest and darkest colors leave no background
        where both fall short."""
        text_bg = v.surfaces[0]
        fields = {"FOREGROUND": fg} | ({"BACKGROUND": bg} if bg else {})
        entries = {"TEXT": {"BACKGROUND": text_bg}, "ATTRIBUTE": fields}
        result = fields | editor_scheme.readable(v, entries).get("ATTRIBUTE", {})
        painted_bg = intellij.opaque(bg or text_bg, text_bg)
        painted_fg = intellij.opaque(result["FOREGROUND"], painted_bg)
        self.assertGreaterEqual(contrast(painted_fg, painted_bg), editor_scheme.MIN_CODE_CONTRAST)


if __name__ == "__main__":
    unittest.main()
