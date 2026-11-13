"""UI themes (`*.theme.json`) as children of JetBrains' Islands themes.

Islands themes paint their controls from named colors (`text-default`,
`layer-0-bg`, `accent-brand-bg`, ...) and color ramps (`gray-10` ... `blue-160`).
The IDE merges a child theme's `colors` over its parent's before it resolves the
names (UIThemeBean.importFromParentTheme), so redefining those names repaints
the whole parent theme. The `ui` section covers the parent keys that use literal
colors instead of names: a few with chosen roles, the rest by remapped_literals.
"""

import re

from . import intellij
from .color import alpha, contrast, mix, rgb
from .variants import Variant

RAMP_STEPS = range(10, 170, 10)
RAMP_NAME = re.compile(r"(gray|blue|green|red|yellow|orange|purple|teal)-\d+|white|black")

# Neutral ramp, dark to light, from Kansō's own background and gray steps.
GRAY_RAMP = (
    "zenBg0", "inkBg0", "zenBg1", "zenBg2", "mistBg1", "zenBg3", "gray5", "pearlGray3",
    "gray4", "gray3", "pearlGray4", "gray2", "fg", "pearlWhite3", "pearlWhite2", "pearlWhite0",
)

# Hue ramps run from a dark tint through a deep (pearl) and a bright (dark-theme)
# Kansō color to a light tint.
HUE_RAMPS = {
    "blue": ("pearlBlue4", "blue"),
    "green": ("pearlGreen", "green"),
    "red": ("pearlRed", "red2"),
    "yellow": ("pearlYellow3", "yellow2"),
    "orange": ("pearlOrange", "orange2"),
    "purple": ("pearlViolet4", "violet"),
    "teal": ("pearlAqua", "green5"),
}


def _hue_ramp(deep: str, bright: str, darkest: str, lightest: str) -> dict[int, str]:
    ramp = {}
    for step in RAMP_STEPS:
        if step <= 70:
            ramp[step] = mix(deep, darkest, 0.85 * (70 - step) / 60)
        elif step <= 100:
            ramp[step] = mix(deep, bright, (step - 70) / 30)
        else:
            ramp[step] = mix(bright, lightest, 0.92 * (step - 100) / 60)
    return ramp


def named_colors(v: Variant) -> dict[str, str]:
    s0, s1, s2, s3 = v.surfaces
    dark = v.dark
    fg = v.ui("fg")
    darkest, lightest = v.color("zenBg0"), v.color("pearlWhite0")
    colors: dict[str, str] = {}

    for step, name in zip(RAMP_STEPS, GRAY_RAMP):
        colors[f"gray-{step}"] = v.color(name)
    for hue, (deep, bright) in HUE_RAMPS.items():
        for step, color in _hue_ramp(v.color(deep), v.color(bright), darkest, lightest).items():
            colors[f"{hue}-{step}"] = color
    colors["white"] = lightest
    colors["black"] = darkest if dark else v.color("pearlBlack0")

    def secondary(color: str, amount: float) -> str:
        return mix(color, s0, amount)

    error, warning, success = v.diag("error"), v.diag("warning"), v.diag("ok")
    brand, selection = v.brand, v.selection
    over_accent = s0 if not dark else darkest

    colors |= {
        "text-default": fg,
        "text-muted": v.ui("fg_dim"),
        "text-secondary": v.syn("comment"),
        "text-disabled": v.ui("nontext"),
        "text-over-accent": over_accent,
        "text-over-accent-inverted": fg,
        "text-link": v.syn("fun"),
        "text-error": error,
        "text-warning": warning,
        "text-success": success,
        "editor-text": fg,
        "accent-brand-bg": brand,
        "accent-brand-border": brand,
        "accent-brand-bg-secondary": secondary(brand, 0.75),
        "accent-brand-border-secondary": secondary(brand, 0.45),
        "accent-error-bg": error,
        "accent-error-border": error,
        "accent-error-bg-secondary": secondary(error, 0.82),
        "accent-error-border-secondary": secondary(error, 0.5),
        "accent-warning-bg": warning,
        "accent-warning-border": warning,
        "accent-warning-bg-secondary": secondary(warning, 0.82),
        "accent-warning-border-secondary": secondary(warning, 0.5),
        "accent-success-bg": success,
        "accent-success-border": success,
        "accent-success-bg-secondary": secondary(success, 0.82),
        "accent-success-border-secondary": secondary(success, 0.5),
        "accent-neutral-bg": v.syn("comment"),
        "accent-ai-bg": secondary(v.syn("keyword"), 0.8),
        "accent-ai-border": v.syn("keyword"),
        "core-bg-transparent-hovered": alpha(fg, 0.09 if dark else 0.07),
        "core-bg-transparent-pressed": alpha(fg, 0.16 if dark else 0.12),
        "core-border-transparent": alpha(fg, 0.13 if dark else 0.12),
        "control-border": s3,
        "control-border-disabled": s2,
        "control-border-raised": v.ui("nontext"),
        "control-bg-small": s3 if dark else s2,
        "control-bg-small-disabled": s2 if dark else s0,
        "control-border-small": v.ui("nontext"),
        "control-bg-raised": s1 if dark else s0,
        "control-error-border-secondary": secondary(error, 0.5),
        "control-warning-border-secondary": secondary(warning, 0.5),
        "toolbar-selected-bg": secondary(brand, 0.6),
        "toolbar-selected-bg-hovered": secondary(brand, 0.45),
        "toolbar-run-bg-hovered": mix(success, s0, 0.2),
        "toolbar-stop-bg-hovered": mix(error, s0, 0.2),
        "selection-bg-active": selection,
        "selection-bg-active-muted": secondary(selection, 0.45),
        "selection-bg-inactive": s2 if dark else s1,
        "selection-bg-hovered": alpha(fg, 0.06 if dark else 0.04),
        "tab-selected-bg-active": secondary(selection, 0.3),
        "tab-selected-bg-inactive": s1,
        "tab-selected-border-active": secondary(brand, 0.3),
        "tab-selected-border-inactive": s3,
        "popup-completion-match-text": v.syn("fun"),
        "search-match-bg": v.search,
        "tree-indent-guide-border": v.ui("indent_line"),
        "icon-default-stroke": v.ui("fg_dim") if dark else v.syn("comment"),
        "icon-disabled": v.ui("nontext"),
        "icon-over-accent": over_accent,
        "icon-green-stroke": success,
        "toggle-on-notch": fg if dark else s0,
    }

    # Islands dark puts editors and tool windows on layer 0 and the frame on layer
    # 1; Islands light puts them on layer 2 and the frame on layer 0.
    if dark:
        colors |= {
            "layer-0-bg": s0, "layer-0-bg-inline": s1, "layer-0-border": s2, "layer-0-border-inline": s2,
            "layer-1-bg": s1, "layer-1-bg-inline": s2, "layer-1-border": s2, "layer-1-border-inline": s3,
            "layer-2-bg": s2, "layer-2-bg-inline": s3, "layer-2-border": s3, "layer-2-border-inline": s3,
            "editor-border-alt": s2, "tool-window-bg-alt": s1, "main-window-bg-alt": s2,
        }
    else:
        colors |= {
            "layer-0-bg": s1, "layer-0-bg-inline": s0, "layer-0-border": s3, "layer-0-border-inline": s2,
            "layer-1-bg": s0, "layer-1-bg-inline": s0, "layer-1-border": s2, "layer-1-border-inline": s2,
            "layer-2-bg": s0, "layer-2-bg-inline": s1, "layer-2-border": s2, "layer-2-border-inline": s2,
            "editor-border-alt": s2, "tool-window-bg-alt": s0, "main-window-bg-alt": s2,
        }
    return colors


def ui_overrides(v: Variant) -> dict:
    """Parent keys with literal colors, pointed at the named colors above."""
    s0, s1, s2, s3 = v.surfaces
    fg = v.ui("fg")
    dark = v.dark
    ui = {
        "Badge": {
            "blueSecondaryBackground": alpha(v.brand, 0.7 if dark else 0.16),
            "greenSecondaryBackground": alpha(v.diag("ok"), 0.7 if dark else 0.16),
            "purpleSecondaryBackground": alpha(v.syn("keyword"), 0.7 if dark else 0.16),
            "graySecondaryBackground": alpha(fg, 0.16 if dark else 0.1),
            "disabledBackground": alpha(fg, 0.16 if dark else 0.1),
            "disabledForeground": alpha(fg, 0.4),
        },
        "Debugger.Variables": {
            "valueForeground": v.syn("string"),
            "collectingDataForeground": "text-disabled",
            "evaluatingExpressionForeground": "text-disabled",
            "changedValueForeground": v.syn("fun"),
            "modifyingValueForeground": v.syn("fun"),
            "errorMessageForeground": "text-error",
            "exceptionForeground": "text-error",
            "typeForeground": "text-secondary",
        },
        "DragAndDrop.rowBackground": alpha(v.brand, 0.15),
        "ToolWindow": {
            "Button.DragAndDrop.buttonDropBackground": alpha(v.brand, 0.5 if dark else 0.25),
            "DragAndDrop.areaBackground": alpha(v.brand, 0.3),
            "DragAndDrop.hintBackground": alpha(v.brand, 0.1),
        },
        "Editor.ToolTip.selectionBackground": "selection-bg-active",
        "List.Tag": {"background": s2 if dark else s1, "foreground": "text-secondary"},
        "Tag.background": s2 if dark else s1,
        "Review": {
            "Branch.Background": s2 if dark else s1,
            "Branch.Background.Hover": s3 if dark else s2,
            "State.Background": s3 if dark else s2,
            "State.Foreground": "text-secondary",
            "ChatItem.Hover": alpha(fg, 0.08),
        },
        "Slider": {
            "buttonColor": v.ui("fg_dim"),
            "buttonBorderColor": s1 if dark else v.syn("comment"),
            "tickColor": "text-secondary",
            "trackColor": s3,
        },
        "VersionControl": {
            "Log.Commit.currentBranchBackground": "selection-bg-active-muted",
            "Log.Commit.unmatchedForeground": "text-disabled",
            "Log.Commit.hoveredBackground": "selection-bg-hovered",
            "Log.Commit.Reference.foreground": "text-secondary",
            "FileHistory.Commit.selectedBranchBackground": "selection-bg-active-muted",
            "MarkerPopup.borderColor": "popup-border",
            "GitLog.headIconColor": v.diag("warning"),
            "GitLog.localBranchIconColor": v.diag("ok"),
            "GitLog.otherIconColor": "text-secondary",
            "GitLog.remoteBranchIconColor": v.syn("keyword"),
            "GitLog.tagIconColor": "text-secondary",
            "Merge.Status.NoConflicts.foreground": "text-success",
        },
        "ParameterInfo": {
            "background": "popup-bg",
            "currentOverloadBackground": "selection-bg-active",
            "borderColor": "popup-border",
            "foreground": "text-default",
            "currentParameterForeground": "text-default",
            "disabledForeground": "text-disabled",
            "infoForeground": "text-secondary",
            "lineSeparatorColor": "popup-border",
        },
        "Tooltip.Learning": {
            "spanBackground": mix(v.brand, s0, 0.3),
            "stepNumberForeground": "text-over-accent",
            "secondaryActionForeground": "text-over-accent",
        },
        # IntelliJ inserts a blue default for these when the child omits them
        # (UIThemeBean.putDefaultsIfAbsent), which would hide the parent's value.
        "ToolWindow.Button.selectedBackground": "toolbar-selected-bg-active",
        "ToolWindow.Button.selectedForeground": "icon-over-accent",
        "EditorTabs.underlineArc": 4,
        # Compact density only: half the gap between islands and smaller corners,
        # so the editor keeps more room. Default density keeps the parent's values.
        "Island.borderWidth.compact": 2,
        "Island.arc.compact": 10,
        "Island.borderArcLength.compact": 6,
    }
    if dark:
        ui["MainWindow.Tab.background"] = s0
    return ui


def icon_palette(v: Variant) -> dict[str, str]:
    s0, _, s2, s3 = v.surfaces
    return {
        "Checkbox.Background.Default": s0,
        "Checkbox.Border.Default": v.ui("nontext"),
        "Checkbox.Foreground.Selected": s0 if not v.dark else v.color("zenBg0"),
        "Checkbox.Background.Selected": v.brand,
        "Checkbox.Border.Selected": v.brand,
        "Checkbox.Focus.Wide": v.brand,
        "Checkbox.Foreground.Disabled": s3,
        "Checkbox.Background.Disabled": s2 if v.dark else s0,
        "Checkbox.Border.Disabled": s3 if v.dark else s2,
    }


def parent_id(v: Variant) -> str:
    return "Islands Dark" if v.dark else "Islands Light"


def _nearest(color: str, candidates: dict[str, str]) -> str:
    r, g, b = rgb(color)

    def distance(item: tuple[str, str]) -> float:
        cr, cg, cb = rgb(item[1][:7])
        return 2 * (r - cr) ** 2 + 4 * (g - cg) ** 2 + 3 * (b - cb) ** 2

    return min(candidates.items(), key=distance)[0]


def _stock_ramp(v: Variant) -> tuple[intellij.Theme, dict[str, str], dict[str, str]]:
    parent = intellij.load(parent_id(v))
    stock = intellij.resolve_colors(parent)
    candidates = {name: color for name, color in stock.items() if RAMP_NAME.fullmatch(name)}
    return parent, stock, candidates


def remapped_names(v: Variant, colors: dict[str, str]) -> dict[str, str]:
    """Stock named colors that Kansō does not define (`Gray12`, `Blue6`, ...).

    Each takes the Kansō value of the ramp color closest to its stock value, so no
    stock color survives through a name."""
    _, stock, candidates = _stock_ramp(v)
    return {
        name: colors[_nearest(value[:7], candidates)] + value[7:]
        for name, value in stock.items()
        if name not in colors and value != intellij.TRANSPARENT
    }


def remapped_literals(v: Variant, colors: dict[str, str], explicit: dict) -> dict[str, str]:
    """Parent `ui` keys that hold a literal color instead of a name.

    Each literal takes the ramp color (`blue-80`, `gray-30`, `white`, ...) that is
    closest to it in the stock theme, with Kansō's value for that ramp name and
    the literal's own opacity. This keeps the parent's light/dark structure.
    """
    parent, _, candidates = _stock_ramp(v)
    skip: dict = {}
    intellij.flatten(explicit, "", skip)
    result = {}
    for key, value in parent.ui.items():
        if key in skip or not (isinstance(value, str) and value.startswith("#") and len(value) in (7, 9)):
            continue
        name = _nearest(value[:7], candidates)
        result[key] = colors[name] + value[7:].upper()
    return result


MIN_TEXT_CONTRAST = 4.5


def _toward(color: str, target: str, other: str) -> str:
    """`color` moved toward `target` until it has 4.5:1 against `other`."""
    step = 0.0
    while contrast(mix(color, target, step), other) < MIN_TEXT_CONTRAST and step < 1:
        step = min(1.0, step + 0.05)
    return mix(color, target, step)


def readable_pairs(v: Variant, theme: dict) -> dict[str, str]:
    """Foreground/background pairs that fall below 4.5:1 once the theme is merged.

    The foreground moves toward Kansō's lightest or darkest color, keeping its
    hue. When even that color is not enough, as on mid-tone accent backgrounds,
    the background also moves away from it."""
    resolved = intellij.resolve_ui(intellij.load(theme))
    base = v.surfaces[0]
    light = v.color("pearlWhite0")
    dark = v.color("zenBg0") if v.dark else v.color("pearlBlack0")
    fixes: dict[str, str] = {}
    for fg_key, bg_key in intellij.text_pairs(resolved):
        bg = intellij.opaque(fixes.get(bg_key, resolved[bg_key]), base)
        fg = intellij.opaque(resolved[fg_key], bg)
        if contrast(fg, bg) >= MIN_TEXT_CONTRAST:
            continue
        target = light if contrast(light, bg) > contrast(dark, bg) else dark
        fg = _toward(fg, target, bg)
        if contrast(fg, bg) < MIN_TEXT_CONTRAST:
            fixes[bg_key] = bg = _toward(bg, dark if target == light else light, fg)
        fixes[fg_key] = fg
    return fixes


def ui_theme(v: Variant) -> dict:
    colors = named_colors(v)
    colors |= remapped_names(v, colors)
    explicit = ui_overrides(v)
    theme = {
        "name": v.name,
        "dark": v.dark,
        "author": "midsorbet; colors from kanso.nvim by webhooked",
        "parentTheme": parent_id(v),
        "editorScheme": f"/schemes/{v.file_stem}.xml",
        "colors": colors,
        "ui": remapped_literals(v, colors, explicit) | explicit,
        "icons": {"ColorPalette": icon_palette(v)},
    }
    theme["ui"] |= readable_pairs(v, theme)
    return theme
