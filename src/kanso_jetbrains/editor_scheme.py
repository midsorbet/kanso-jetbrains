"""Editor color schemes (`.xml`), mapped from kanso.nvim's highlight groups.

Each attribute follows the Neovim group that covers the same construct
(highlights/syntax.lua, treesitter.lua, editor.lua in kanso.nvim). kanso.nvim
italicizes comments and keywords by default; the schemes do the same. Entries of
the parent scheme that these do not cover are remapped (remapped_stock), so no
stock color shows.
"""

from collections import Counter
from dataclasses import dataclass
from xml.etree import ElementTree as ET

from . import intellij
from .color import contrast, mix, rgb
from .variants import Variant

# TextAttributes serialization values.
BOLD, ITALIC = 1, 2
EFFECT_UNDERSCORE, EFFECT_WAVE, EFFECT_STRIKEOUT = 1, 2, 3
ANSI_NAMES = ("BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "WHITE")


@dataclass(frozen=True)
class Attr:
    fg: str | None = None
    bg: str | None = None
    font: int = 0
    effect: str | None = None
    effect_type: int | None = None
    stripe: str | None = None


def _hex(color: str) -> str:
    return color.removeprefix("#").lower()


def colors(v: Variant) -> dict[str, str]:
    s0, s1, s2, _ = v.surfaces
    added, changed, removed = v.vcs("added"), v.vcs("changed"), v.vcs("removed")
    return {
        "CARET_COLOR": v.ui("cursor_bg"),
        "CARET_ROW_COLOR": v.ui("bg_p2") if v.dark else v.ui("bg_p1"),
        "SELECTION_BACKGROUND": v.selection,
        "SELECTION_FOREGROUND": "",
        "LINE_NUMBERS_COLOR": v.ui("cursor_line_nr_foreground"),
        "LINE_NUMBER_ON_CARET_ROW_COLOR": v.ui("cursor_line_nr_active_foreground"),
        "GUTTER_BACKGROUND": s0,
        "INDENT_GUIDE": v.ui("indent_line"),
        "SELECTED_INDENT_GUIDE": v.ui("active_indent_line") if v.dark else v.color("pearlWhite3"),
        "WHITESPACES": v.ui("whitespace"),
        "SOFT_WRAP_SIGN_COLOR": v.ui("nontext"),
        "RIGHT_MARGIN_COLOR": s1,
        "METHOD_SEPARATORS_COLOR": s2,
        "TEARLINE_COLOR": s2,
        "SELECTED_TEARLINE_COLOR": v.ui("nontext"),
        "FOLDED_TEXT_BORDER_COLOR": "",
        "VISUAL_INDENT_GUIDE": v.ui("indent_line"),
        "DOCUMENTATION_COLOR": s1,
        "LOOKUP_COLOR": s1,
        "ERROR_HINT": s1,
        "INFORMATION_HINT": s1,
        "QUESTION_HINT": s1,
        "NOTIFICATION_BACKGROUND": s1,
        "CONSOLE_BACKGROUND_KEY": s0,
        "ADDED_LINES_COLOR": added,
        "MODIFIED_LINES_COLOR": changed,
        "DELETED_LINES_COLOR": removed,
        "WHITESPACES_MODIFIED_LINES_COLOR": changed,
        "IGNORED_ADDED_LINES_BORDER_COLOR": added,
        "IGNORED_MODIFIED_LINES_BORDER_COLOR": changed,
        "IGNORED_DELETED_LINES_BORDER_COLOR": removed,
        "DIFF_SEPARATORS_BACKGROUND": s1,
        "FILESTATUS_ADDED": added,
        "FILESTATUS_COPIED": added,
        "FILESTATUS_DELETED": removed,
        "FILESTATUS_MODIFIED": changed,
        "FILESTATUS_RENAMED": changed,
        "FILESTATUS_MERGED": v.syn("keyword"),
        "FILESTATUS_UNKNOWN": v.vcs("untracked"),
        "FILESTATUS_IDEA_FILESTATUS_IGNORED": v.syn("comment"),
        "FILESTATUS_IDEA_FILESTATUS_DELETED_FROM_FILE_SYSTEM": removed,
        "FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_CONFLICTS": v.diag("error"),
        "FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_BOTH_CONFLICTS": v.diag("error"),
        "FILESTATUS_IDEA_FILESTATUS_MERGED_WITH_PROPERTY_CONFLICTS": v.diag("error"),
        "FILESTATUS_addedOutside": added,
        "FILESTATUS_modifiedOutside": changed,
        "FILESTATUS_changelistConflict": v.diag("error"),
        "FILESTATUS_NOT_CHANGED_IMMEDIATE": changed,
        "FILESTATUS_NOT_CHANGED_RECURSIVE": changed,
    }


def attributes(v: Variant) -> dict[str, Attr]:
    fg = v.ui("fg")
    syn = v.syn
    s0, s1, s2, _ = v.surfaces
    comment = Attr(fg=syn("comment"), font=ITALIC)
    punct = Attr(fg=syn("punct"))
    attrs = {
        "TEXT": Attr(fg=fg, bg=s0),
        "FOLDED_TEXT_ATTRIBUTES": Attr(fg=v.ui("special"), bg=s1),
        # Language defaults. Language-specific keys inherit these in the parent scheme.
        "DEFAULT_KEYWORD": Attr(fg=syn("keyword"), font=ITALIC),
        "DEFAULT_LINE_COMMENT": comment,
        "DEFAULT_BLOCK_COMMENT": comment,
        "DEFAULT_DOC_COMMENT": comment,
        "DEFAULT_DOC_COMMENT_TAG": Attr(fg=syn("special1"), font=ITALIC),
        "DEFAULT_DOC_COMMENT_TAG_VALUE": Attr(fg=syn("parameter"), font=ITALIC),
        "DEFAULT_DOC_MARKUP": Attr(fg=syn("comment")),
        "DEFAULT_STRING": Attr(fg=syn("string")),
        "DEFAULT_VALID_STRING_ESCAPE": Attr(fg=syn("regex")),
        "DEFAULT_INVALID_STRING_ESCAPE": Attr(fg=syn("regex"), effect=v.diag("error"), effect_type=EFFECT_WAVE),
        "DEFAULT_NUMBER": Attr(fg=syn("number")),
        "DEFAULT_CONSTANT": Attr(fg=syn("constant")),
        "DEFAULT_IDENTIFIER": Attr(fg=fg),
        "DEFAULT_LOCAL_VARIABLE": Attr(fg=fg),
        "DEFAULT_REASSIGNED_LOCAL_VARIABLE": Attr(fg=fg, effect=syn("comment"), effect_type=EFFECT_UNDERSCORE),
        "DEFAULT_PARAMETER": Attr(fg=syn("parameter")),
        "DEFAULT_REASSIGNED_PARAMETER": Attr(fg=syn("parameter"), effect=syn("comment"), effect_type=EFFECT_UNDERSCORE),
        "DEFAULT_INSTANCE_FIELD": Attr(fg=syn("identifier")),
        "DEFAULT_STATIC_FIELD": Attr(fg=syn("identifier"), font=ITALIC),
        "DEFAULT_GLOBAL_VARIABLE": Attr(fg=syn("constant")),
        "DEFAULT_FUNCTION_DECLARATION": Attr(fg=syn("fun")),
        "DEFAULT_FUNCTION_CALL": Attr(fg=syn("fun")),
        "DEFAULT_INSTANCE_METHOD": Attr(fg=syn("fun")),
        "DEFAULT_STATIC_METHOD": Attr(fg=syn("fun"), font=ITALIC),
        "DEFAULT_CLASS_NAME": Attr(fg=syn("type")),
        "DEFAULT_CLASS_REFERENCE": Attr(fg=syn("type")),
        "DEFAULT_INTERFACE_NAME": Attr(fg=syn("type"), font=ITALIC),
        "DEFAULT_PREDEFINED_SYMBOL": Attr(fg=syn("special2"), font=ITALIC),
        "DEFAULT_METADATA": Attr(fg=syn("constant")),
        "DEFAULT_LABEL": Attr(fg=syn("special1")),
        "DEFAULT_OPERATION_SIGN": Attr(fg=syn("operator")),
        "DEFAULT_BRACES": punct,
        "DEFAULT_BRACKETS": punct,
        "DEFAULT_PARENTHS": punct,
        "DEFAULT_COMMA": punct,
        "DEFAULT_SEMICOLON": punct,
        "DEFAULT_DOT": punct,
        "DEFAULT_TAG": Attr(fg=syn("special1")),
        "DEFAULT_ATTRIBUTE": Attr(fg=syn("identifier")),
        "DEFAULT_ENTITY": Attr(fg=syn("special1")),
        "DEFAULT_TEMPLATE_LANGUAGE_COLOR": Attr(fg=fg),
        "DEFAULT_HIGHLIGHTED_REFERENCE": Attr(bg=v.ui("bg_p2")),
        # Markdown, as kanso.nvim's @markup groups.
        "MARKDOWN_HEADER_LEVEL_1": Attr(fg=syn("fun"), font=BOLD),
        "MARKDOWN_HEADER_LEVEL_2": Attr(fg=syn("fun"), font=BOLD),
        "MARKDOWN_HEADER_LEVEL_3": Attr(fg=syn("fun"), font=BOLD),
        "MARKDOWN_HEADER_LEVEL_4": Attr(fg=syn("fun")),
        "MARKDOWN_HEADER_LEVEL_5": Attr(fg=syn("fun")),
        "MARKDOWN_HEADER_LEVEL_6": Attr(fg=syn("fun")),
        "MARKDOWN_CODE_SPAN": Attr(fg=syn("string")),
        "MARKDOWN_CODE_BLOCK": Attr(fg=syn("string")),
        "MARKDOWN_BLOCK_QUOTE": Attr(fg=syn("parameter")),
        "MARKDOWN_LINK_TEXT": Attr(fg=syn("special1"), effect=syn("special1"), effect_type=EFFECT_UNDERSCORE),
        "MARKDOWN_LINK_DESTINATION": Attr(fg=syn("comment")),
        "MARKDOWN_BOLD": Attr(font=BOLD),
        "MARKDOWN_ITALIC": Attr(font=ITALIC),
        # Diagnostics and inspections.
        "ERRORS_ATTRIBUTES": Attr(effect=v.diag("error"), effect_type=EFFECT_WAVE, stripe=v.diag("error")),
        "WARNING_ATTRIBUTES": Attr(effect=v.diag("warning"), effect_type=EFFECT_WAVE, stripe=v.diag("warning")),
        "WEAK_WARNING_ATTRIBUTES": Attr(effect=v.diag("info"), effect_type=EFFECT_WAVE, stripe=v.diag("info")),
        "INFO_ATTRIBUTES": Attr(effect=v.diag("hint"), effect_type=EFFECT_UNDERSCORE),
        "TYPO": Attr(effect=v.diag("hint"), effect_type=EFFECT_WAVE),
        "GRAMMAR_ERROR": Attr(effect=v.diag("hint"), effect_type=EFFECT_WAVE),
        "WRONG_REFERENCES_ATTRIBUTES": Attr(fg=v.diag("error")),
        "DEPRECATED_ATTRIBUTES": Attr(effect=syn("deprecated"), effect_type=EFFECT_STRIKEOUT),
        "MARKED_FOR_REMOVAL_ATTRIBUTES": Attr(effect=v.diag("error"), effect_type=EFFECT_STRIKEOUT),
        "NOT_USED_ELEMENT_ATTRIBUTES": Attr(fg=syn("deprecated")),
        "TODO_DEFAULT_ATTRIBUTES": Attr(fg=v.diag("info"), font=BOLD | ITALIC, stripe=v.diag("info")),
        # Search, references, braces, links.
        "SEARCH_RESULT_ATTRIBUTES": Attr(bg=v.search, stripe=v.search),
        "WRITE_SEARCH_RESULT_ATTRIBUTES": Attr(bg=v.search, stripe=v.search),
        "TEXT_SEARCH_RESULT_ATTRIBUTES": Attr(bg=v.search, stripe=v.search),
        "IDENTIFIER_UNDER_CARET_ATTRIBUTES": Attr(bg=v.ui("bg_p2") if v.dark else s2, stripe=v.ui("nontext")),
        "WRITE_IDENTIFIER_UNDER_CARET_ATTRIBUTES": Attr(
            bg=v.ui("bg_p2") if v.dark else s2, effect=v.ui("nontext"), effect_type=EFFECT_UNDERSCORE, stripe=v.diag("warning")
        ),
        "MATCHED_BRACE_ATTRIBUTES": Attr(fg=v.diag("warning"), font=BOLD),
        "UNMATCHED_BRACE_ATTRIBUTES": Attr(fg=v.diag("error"), font=BOLD),
        "HYPERLINK_ATTRIBUTES": Attr(fg=syn("special1"), effect=syn("special1"), effect_type=EFFECT_UNDERSCORE),
        "FOLLOWED_HYPERLINK_ATTRIBUTES": Attr(fg=syn("keyword"), effect=syn("keyword"), effect_type=EFFECT_UNDERSCORE),
        "CTRL_CLICKABLE": Attr(fg=syn("fun"), effect=syn("fun"), effect_type=EFFECT_UNDERSCORE),
        "INLAY_DEFAULT": Attr(fg=syn("comment"), bg=s1),
        "INLINE_PARAMETER_HINT": Attr(fg=syn("comment"), bg=s1),
        "INLINE_PARAMETER_HINT_CURRENT": Attr(fg=fg, bg=s2, font=BOLD),
        "INLINE_PARAMETER_HINT_HIGHLIGHTED": Attr(fg=fg, bg=s2),
        "INLAY_TEXT_WITHOUT_BACKGROUND": Attr(fg=syn("comment")),
        # Debugger.
        "BREAKPOINT_ATTRIBUTES": Attr(bg=v.diff("delete"), stripe=v.diag("error")),
        "EXECUTIONPOINT_ATTRIBUTES": Attr(bg=v.search),
        "DEBUGGER_INLINED_VALUES": Attr(fg=syn("comment"), font=ITALIC),
        # Diffs, as kanso.nvim's Diff groups.
        "DIFF_INSERTED": Attr(bg=v.diff("add"), stripe=v.vcs("added")),
        "DIFF_DELETED": Attr(bg=v.diff("delete"), stripe=v.vcs("removed")),
        "DIFF_MODIFIED": Attr(bg=v.diff("change"), stripe=v.vcs("changed")),
        "DIFF_CONFLICT": Attr(bg=v.diff("text"), stripe=v.diag("error")),
        # Console, from kanso.nvim's terminal colors.
        "CONSOLE_NORMAL_OUTPUT": Attr(fg=fg),
        "CONSOLE_ERROR_OUTPUT": Attr(fg=v.diag("error")),
        "CONSOLE_SYSTEM_OUTPUT": Attr(fg=v.ui("fg_dim")),
        "CONSOLE_USER_INPUT": Attr(fg=syn("string"), font=ITALIC),
        "LOG_ERROR_OUTPUT": Attr(fg=v.diag("error")),
        "LOG_WARNING_OUTPUT": Attr(fg=v.diag("warning")),
        "LOG_INFO_OUTPUT": Attr(fg=fg),
        "LOG_DEBUG_OUTPUT": Attr(fg=syn("comment")),
        "LOG_VERBOSE_OUTPUT": Attr(fg=syn("comment")),
        "LOG_EXPIRED_ENTRY": Attr(fg=v.ui("nontext")),
    }
    ansi = ("BLACK", "RED", "GREEN", "YELLOW", "BLUE", "MAGENTA", "CYAN", "GRAY")
    for index, name in enumerate(ansi):
        attrs[f"CONSOLE_{name}_OUTPUT"] = Attr(fg=v.term(index))
    bright = ("DARKGRAY", "RED_BRIGHT", "GREEN_BRIGHT", "YELLOW_BRIGHT", "BLUE_BRIGHT", "MAGENTA_BRIGHT", "CYAN_BRIGHT", "WHITE")
    for index, name in enumerate(bright, start=8):
        attrs[f"CONSOLE_{name}_OUTPUT"] = Attr(fg=v.term(index))
    # The terminal's ANSI slots: the foreground for text, the background for
    # background colors.
    for index, name in enumerate(ANSI_NAMES):
        attrs[f"BLOCK_TERMINAL_{name}"] = Attr(fg=v.term(index), bg=v.term(index))
        attrs[f"BLOCK_TERMINAL_{name}_BRIGHT"] = Attr(fg=v.term(index + 8), bg=v.term(index + 8))
    attrs["BLOCK_TERMINAL_COMMAND"] = Attr(fg=fg, font=BOLD)
    attrs["BLOCK_TERMINAL_SEARCH_ENTRY"] = Attr(fg=fg, bg=v.search)
    attrs["BLOCK_TERMINAL_CURRENT_SEARCH_ENTRY"] = Attr(fg=s0, bg=v.diag("warning"))
    attrs["BLOCK_TERMINAL_GENERATE_COMMAND_PROMPT_TEXT"] = Attr(fg=syn("keyword"))
    return attrs


def parent_scheme(v: Variant) -> str:
    return "Darcula" if v.dark else "Default"


def attribute_fields(attr: Attr) -> dict[str, str]:
    fields = {
        "FOREGROUND": attr.fg,
        "BACKGROUND": attr.bg,
        "FONT_TYPE": str(attr.font) if attr.font else None,
        "EFFECT_COLOR": attr.effect,
        "EFFECT_TYPE": str(attr.effect_type) if attr.effect_type is not None else None,
        "ERROR_STRIPE_COLOR": attr.stripe,
    }
    return {key: value for key, value in fields.items() if value is not None}


class _StockMap:
    """Stock color -> Kansō color, learned from the keys that both schemes set.

    A stock color without a pair takes the pair of the closest stock color."""

    def __init__(self) -> None:
        self.pairs: dict[str, Counter] = {}

    def learn(self, stock: str | None, kanso: str | None) -> None:
        if stock and kanso:
            self.pairs.setdefault(stock[:7], Counter())[kanso[:7]] += 1

    def __call__(self, stock: str) -> str:
        solid, opacity = stock[:7], stock[7:]
        if solid not in self.pairs:
            r, g, b = rgb(solid)
            solid = min(self.pairs, key=lambda c: sum(w * (x - y) ** 2 for w, x, y in zip((2, 4, 3), (r, g, b), rgb(c))))
        return self.pairs[solid].most_common(1)[0][0] + opacity


def _group(field: str) -> str:
    return {"FOREGROUND": "fg", "BACKGROUND": "bg"}.get(field, "mark")


# Name parts that mean the same construct in language keys and DEFAULT_* keys.
_SAME_WORDS = {"ANNOTATION": "METADATA", "FUNCTION": "FUNCTION", "METHOD": "FUNCTION"}


def _inherited_default(key: str, fields: dict, defaults: dict[str, dict]) -> str | None:
    """The DEFAULT_* key this key stands for: the same name without _ATTRIBUTES
    (Darcula's INSTANCE_FIELD_ATTRIBUTES), or the same stock colors with a shared
    name part (ANNOTATION_NAME_ATTRIBUTES uses DEFAULT_METADATA's yellow)."""
    named = "DEFAULT_" + key.removesuffix("_ATTRIBUTES")
    if named in defaults:
        return named
    look = {f: fields.get(f) for f in ("FOREGROUND", "BACKGROUND")}
    words = {_SAME_WORDS.get(w, w) for w in key.replace(".", "_").split("_")}
    for default, default_fields in defaults.items():
        if look["FOREGROUND"] and look == {f: default_fields.get(f) for f in look} and words & set(default.split("_")[1:]):
            return default
    return None


def remapped_stock(v: Variant, own_colors: dict[str, str], own_attributes: dict[str, dict]) -> tuple[dict, dict]:
    """The parent scheme's entries that Kansō does not set (Default or Darcula plus
    the attributes that bundled plugins add). An entry that copies a DEFAULT_*
    look inherits Kansō's version of it; the rest get their colors replaced."""
    base = intellij.bundled_scheme(parent_scheme(v))
    maps = {"fg": _StockMap(), "bg": _StockMap(), "mark": _StockMap()}
    colors = _StockMap()
    for key, fields in own_attributes.items():
        stock = base.attributes.get(key, {})
        for field in intellij.COLOR_FIELDS:
            maps[_group(field)].learn(stock.get(field), fields.get(field))
    maps["mark"].pairs = {**maps["fg"].pairs, **maps["mark"].pairs}
    for key, value in own_colors.items():
        colors.learn(base.colors.get(key), value or None)

    defaults = {k: f for k, f in base.attributes.items() if k.startswith("DEFAULT_") and k in own_attributes}
    extra_attributes = {}
    for key, fields in base.attributes.items():
        if key in own_attributes or "baseAttributes" in fields:
            continue
        default = _inherited_default(key, fields, defaults)
        if default and fields.get("FONT_TYPE") == base.attributes[default].get("FONT_TYPE"):
            extra_attributes[key] = {"baseAttributes": default}
            continue
        if default:
            # Same colors as the default, different weight or slant: keep the stock style.
            style = {f: fields[f] for f in ("FONT_TYPE", "EFFECT_TYPE") if fields.get(f) is not None}
            extra_attributes[key] = own_attributes[default] | style
            continue
        extra_attributes[key] = {
            field: maps[_group(field)](value) if field in intellij.COLOR_FIELDS else value
            for field, value in fields.items()
            if value is not None
        }
    extra_colors = {key: colors(value) for key, value in base.colors.items() if key not in own_colors and value}
    return extra_colors, extra_attributes


MIN_CODE_CONTRAST = 3.0


def is_palette_slot(key: str) -> bool:
    """ANSI color slots: their foreground and background are separate colors, and
    black matches the background in kanso.nvim's terminal palette."""
    return key == "CONSOLE_BLACK_OUTPUT" or (key.startswith("BLOCK_TERMINAL_") and key.split("_", 2)[2].split("_")[0] in ANSI_NAMES)


def readable(v: Variant, entries: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:
    """Text below 3:1 on its background moves toward Kansō's lightest or darkest
    color, keeping its hue. In pearl this darkens the orange warning color."""
    text_bg = entries["TEXT"]["BACKGROUND"]
    light = v.color("pearlWhite0")
    dark = v.color("zenBg0") if v.dark else v.color("pearlBlack0")
    fixed = {}
    for key, fields in entries.items():
        fg = fields.get("FOREGROUND")
        if not fg or is_palette_slot(key):
            continue
        bg = intellij.opaque(fields.get("BACKGROUND") or text_bg, text_bg)
        solid = intellij.opaque(fg, bg)
        if contrast(solid, bg) >= MIN_CODE_CONTRAST:
            continue
        target = light if contrast(light, bg) > contrast(dark, bg) else dark
        step = 0.0
        while contrast(mix(solid, target, step), bg) < MIN_CODE_CONTRAST and step < 1:
            step = min(1.0, step + 0.05)
        fixed[key] = fields | {"FOREGROUND": mix(solid, target, step)}
    return fixed


def scheme_entries(v: Variant) -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    own_colors = colors(v)
    own_attributes = {key: attribute_fields(attr) for key, attr in attributes(v).items()}
    extra_colors, extra_attributes = remapped_stock(v, own_colors, own_attributes)
    entries = own_attributes | extra_attributes
    return own_colors | extra_colors, entries | readable(v, entries)


def editor_scheme(v: Variant) -> str:
    scheme = ET.Element("scheme", name=v.name, version="142", parent_scheme=parent_scheme(v))
    meta = ET.SubElement(scheme, "metaInfo")
    ET.SubElement(meta, "property", name="ide").text = "idea"
    ET.SubElement(meta, "property", name="originalScheme").text = v.name

    all_colors, all_attributes = scheme_entries(v)
    color_element = ET.SubElement(scheme, "colors")
    for name, value in sorted(all_colors.items()):
        ET.SubElement(color_element, "option", name=name, value=_hex(value) if value else "")

    attributes_element = ET.SubElement(scheme, "attributes")
    for name, fields in sorted(all_attributes.items()):
        option = ET.SubElement(attributes_element, "option", name=name)
        if "baseAttributes" in fields:
            option.set("baseAttributes", fields["baseAttributes"])
            continue
        value = ET.SubElement(option, "value")
        for key, setting in fields.items():
            ET.SubElement(value, "option", name=key, value=_hex(setting) if key in intellij.COLOR_FIELDS else setting)

    ET.indent(scheme, space="  ")
    return ET.tostring(scheme, encoding="unicode") + "\n"
