"""Checks on the themes as IntelliJ 263.7307.200 merges them with its own themes.

kanso_jetbrains.intellij follows the IDE's loading code; intellij/<build>/ holds
the parent themes and schemes of that build. A failure here names the key and
color, so a mistake shows without opening the IDE.
"""

import io
import json
import re
import tempfile
import unittest
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

from kanso_jetbrains import editor_scheme, intellij
from kanso_jetbrains.color import contrast
from kanso_jetbrains.plugin import plugin_files, write_jar
from kanso_jetbrains.ui_theme import MIN_TEXT_CONTRAST, ui_theme
from kanso_jetbrains.variants import load_variants

PALETTE = Path(__file__).resolve().parent.parent / "palette" / "kanso.json"
VARIANTS = load_variants(PALETTE)

# Named colors that the themes reference but leave to the Islands parents.
PARENT_NAMES = {"popup-bg", "popup-border", "toolbar-selected-bg-active"}

HEX = re.compile(r"#[0-9A-F]{6}([0-9A-F]{2})?")


def flat_ui(theme: dict) -> dict:
    values: dict = {}
    intellij.flatten(theme["ui"], "", values)
    return values


def emitted_colors(theme: dict) -> set[str]:
    """Every color that our theme file itself contains, without opacity."""
    values = list(theme["colors"].values()) + list(flat_ui(theme).values()) + list(theme["icons"]["ColorPalette"].values())
    return {value[:7].upper() for value in values if isinstance(value, str) and value.startswith("#")}


class UiThemeTest(unittest.TestCase):
    def test_color_values_are_hex_or_known_names(self):
        # An unknown name resolves to a transparent color in the IDE, with only a log warning.
        for v in VARIANTS:
            theme = ui_theme(v)
            names = set(theme["colors"]) | PARENT_NAMES
            for key, value in list(theme["colors"].items()) + list(flat_ui(theme).items()):
                if isinstance(value, str):
                    with self.subTest(variant=v.key, key=key):
                        self.assertTrue(HEX.fullmatch(value) or value in names, value)

    def test_no_stock_color_survives_the_merge(self):
        for v in VARIANTS:
            theme = ui_theme(v)
            ours = emitted_colors(theme)
            for key, color in intellij.resolve_ui(intellij.load(theme)).items():
                with self.subTest(variant=v.key, key=key):
                    self.assertIn(color[:7], ours, f"{key} keeps the stock color {color}")

    def test_text_is_readable_on_its_background(self):
        for v in VARIANTS:
            resolved = intellij.resolve_ui(intellij.load(ui_theme(v)))
            base = v.surfaces[0]
            pairs = intellij.text_pairs(resolved)
            self.assertGreater(len(pairs), 50)
            for fg_key, bg_key in pairs:
                bg = intellij.opaque(resolved[bg_key], base)
                fg = intellij.opaque(resolved[fg_key], bg)
                with self.subTest(variant=v.key, key=fg_key):
                    self.assertGreaterEqual(contrast(fg, bg), MIN_TEXT_CONTRAST, f"{fg} on {bg}")

    def test_body_text_and_accents(self):
        for v in VARIANTS:
            colors = ui_theme(v)["colors"]
            editor_bg = v.surfaces[0]
            with self.subTest(variant=v.key):
                self.assertGreaterEqual(contrast(colors["text-default"], editor_bg), 7)
                self.assertGreaterEqual(contrast(colors["text-over-accent"], colors["accent-brand-bg"]), 4.5)
                self.assertGreaterEqual(contrast(colors["text-default"], colors["selection-bg-active"]), 4.5)


class EditorSchemeTest(unittest.TestCase):
    def effective(self, v):
        own = intellij.read_scheme_xml(editor_scheme.editor_scheme(v))
        return own, intellij.effective_scheme(own, editor_scheme.parent_scheme(v))

    def test_no_stock_color_survives_the_merge(self):
        for v in VARIANTS:
            own, effective = self.effective(v)
            ours = {c[:7] for c in own.colors.values() if c}
            ours |= {c[:7] for fields in own.attributes.values() for f, c in fields.items() if f in intellij.COLOR_FIELDS and c}
            for key, color in effective.colors.items():
                if color:
                    with self.subTest(variant=v.key, color=key):
                        self.assertIn(color[:7], ours)
            for key, fields in effective.attributes.items():
                for field, color in fields.items():
                    if field in intellij.COLOR_FIELDS and color:
                        with self.subTest(variant=v.key, attribute=key, field=field):
                            self.assertIn(color[:7], ours)

    def test_inherited_attributes_exist(self):
        for v in VARIANTS:
            own, _ = self.effective(v)
            for key, fields in own.attributes.items():
                base = fields.get("baseAttributes")
                if base:
                    with self.subTest(variant=v.key, attribute=key):
                        self.assertIn(base, own.attributes)

    def test_code_is_readable(self):
        for v in VARIANTS:
            _, effective = self.effective(v)
            text_bg = effective.attributes["TEXT"]["BACKGROUND"]
            for key, fields in effective.attributes.items():
                fg = fields.get("FOREGROUND")
                if not fg or editor_scheme.is_palette_slot(key):
                    continue
                bg = intellij.opaque(fields.get("BACKGROUND") or text_bg, text_bg)
                with self.subTest(variant=v.key, attribute=key):
                    self.assertGreaterEqual(contrast(intellij.opaque(fg, bg), bg), editor_scheme.MIN_CODE_CONTRAST)


class JarTest(unittest.TestCase):
    def test_jar_holds_every_referenced_file(self):
        with tempfile.TemporaryDirectory() as directory:
            jar_path = Path(directory) / "kanso.jar"
            write_jar(jar_path, plugin_files("0.0.0", VARIANTS))
            with zipfile.ZipFile(jar_path) as jar:
                names = set(jar.namelist())
                plugin = ET.fromstring(jar.read("META-INF/plugin.xml"))
                providers = plugin.findall("./extensions/themeProvider")
                self.assertEqual(len(providers), len(VARIANTS))
                for provider in providers:
                    path = provider.get("path").removeprefix("/")
                    self.assertIn(path, names)
                    theme = json.load(io.BytesIO(jar.read(path)))
                    scheme_path = theme["editorScheme"].removeprefix("/")
                    self.assertIn(scheme_path, names)
                    scheme = ET.fromstring(jar.read(scheme_path))
                    self.assertEqual(scheme.get("name"), theme["name"])

    def test_jar_is_reproducible(self):
        files = plugin_files("0.0.0", VARIANTS)
        with tempfile.TemporaryDirectory() as directory:
            first, second = Path(directory) / "a.jar", Path(directory) / "b.jar"
            write_jar(first, files)
            write_jar(second, files)
            self.assertEqual(first.read_bytes(), second.read_bytes())


if __name__ == "__main__":
    unittest.main()
