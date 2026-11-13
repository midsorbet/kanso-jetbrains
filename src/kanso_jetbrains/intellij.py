"""IntelliJ's theme loading, reduced to what decides colors.

This follows platform/platform-impl/src/com/intellij/ide/ui/UIThemeBean.kt and
UITheme.kt of the pinned build (see BUILD): the `ui` section is flattened, a
child is merged over its already-merged parent (parent first, child overrides),
then names in `colors` are resolved, and `ui` values that name a color take that
color. An unknown name resolves to transparent, as in the IDE.

The parent theme files in intellij/<BUILD>/ are copied unchanged from
JetBrains/intellij-community (Apache-2.0) by scripts/update-intellij.sh.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

from .color import mix

BUILD = "263.7307.200"
PARENT_DIR = Path(__file__).resolve().parents[2] / "intellij" / BUILD

# themeProvider ids of the bundled themes (intellij.platform.ide.impl.xml).
BUNDLED = {
    "Darcula": "darcula.theme.json",
    "IntelliJ": "intellijlaf.theme.json",
    "ExperimentalDark": "expUI_dark.theme.json",
    "ExperimentalLight": "expUI_light.theme.json",
    "ExperimentalLightWithLightHeader": "expUI_light_with_light_header.theme.json",
    "Islands Dark": "ManyIslandsDark.theme.json",
    "Islands Light": "ManyIslandsLight.theme.json",
}

TRANSPARENT = "#00000000"
OS_KEY = "os.windows"  # Delcatty runs the IDE on Windows.


@dataclass
class Theme:
    name: str
    dark: bool
    parent: str | None
    ui: dict[str, object] = field(default_factory=dict)
    colors: dict[str, str] = field(default_factory=dict)
    palette: dict[str, str] = field(default_factory=dict)


def flatten(node: dict, prefix: str, out: dict) -> None:
    for key, value in node.items():
        if isinstance(value, dict) and any(k.startswith("os.") for k in value):
            chosen = value.get(OS_KEY, value.get("os.default"))
            if chosen is not None:
                out[_join(prefix, key)] = chosen
            continue
        if isinstance(value, dict):
            flatten(value, _join(prefix, key), out)
        else:
            out[_join(prefix, key)] = value


def _join(prefix: str, key: str) -> str:
    if not prefix:
        return key
    return prefix + key if key == "UI" else f"{prefix}.{key}"


def read_theme(data: dict) -> Theme:
    ui: dict[str, object] = {}
    flatten(data.get("ui", {}), "", ui)
    # UIThemeBean.putDefaultsIfAbsent (new UI): a child that omits these replaces
    # the parent's value with JetBrains blue.
    ui.setdefault("EditorTabs.underlineArc", 4)
    ui.setdefault("ToolWindow.Button.selectedBackground", "#3573F0")
    ui.setdefault("ToolWindow.Button.selectedForeground", "#FFFFFF")
    palette = dict(data.get("icons", {}).get("ColorPalette", {}))
    return Theme(data["name"], bool(data.get("dark", False)), data.get("parentTheme"), ui, dict(data.get("colors", {})), palette)


def _merge(child: dict, parent: dict) -> dict:
    merged = {k: v for k, v in parent.items() if k not in child}
    merged.update(child)
    return merged


def load(theme_id_or_data: str | dict) -> Theme:
    """The merged theme, as UITheme.createTheme builds it."""
    if isinstance(theme_id_or_data, str):
        theme = read_theme(json.loads((PARENT_DIR / BUNDLED[theme_id_or_data]).read_text()))
        is_darcula = theme_id_or_data == "Darcula"
    else:
        theme = read_theme(theme_id_or_data)
        is_darcula = False
    if is_darcula:
        return theme
    parent_id = theme.parent or ("Darcula" if theme.dark else "IntelliJ")
    parent = load(parent_id)
    theme.ui = _merge(theme.ui, parent.ui)
    theme.colors = _merge(theme.colors, parent.colors)
    theme.palette = _merge(theme.palette, parent.palette)
    return theme


def resolve_colors(theme: Theme) -> dict[str, str]:
    """initializeNamedColors: hex values first, then aliases in two passes."""
    resolved = {k: v.upper() for k, v in theme.colors.items() if isinstance(v, str) and v.startswith("#")}
    for _ in range(2):
        for key, value in theme.colors.items():
            if key not in resolved and value in resolved:
                resolved[key] = resolved[value]
    for key in theme.colors:
        resolved.setdefault(key, TRANSPARENT)
    return resolved


def resolve_ui(theme: Theme) -> dict[str, str]:
    """Every `ui` key that ends up as a color, with its #RRGGBB[AA] value."""
    colors = resolve_colors(theme)
    result = {}
    for key, value in theme.ui.items():
        if not isinstance(value, str):
            continue
        if value in colors:
            result[key] = colors[value]
        elif value.startswith("#") and len(value) in (7, 9):
            result[key] = value.upper()
    return result


# Foregrounds that are meant to recede; WCAG exempts disabled controls.
_MUTED = ("disabled", "inactive", "placeholder", "shadow", "separator")


def text_pairs(resolved: dict[str, str]) -> list[tuple[str, str]]:
    """(foreground key, background key) pairs that share a prefix, such as
    `List.selectionForeground` and `List.selectionBackground`."""
    pairs = []
    for key in resolved:
        if any(word in key.lower() for word in _MUTED):
            continue
        for fg, bg in (("foreground", "background"), ("Foreground", "Background")):
            if key.endswith(fg):
                partner = key[: -len(fg)] + bg
                if partner in resolved:
                    pairs.append((key, partner))
    return pairs


def opaque(color: str, base: str) -> str:
    """A #RRGGBBAA color painted over `base`."""
    if len(color) == 9:
        return mix(base, color[:7], int(color[7:], 16) / 255)
    return color


# Editor color schemes ========================================================
#
# A scheme entry replaces the parent's entry for the same key as a whole. Bundled
# plugins add attributes to Default and Darcula (additionalTextAttributes) where
# the scheme does not define them. Scheme files write colors as hex without
# leading zeros ("90618" is #090618) or leave a value out for "no color".

COLOR_FIELDS = ("FOREGROUND", "BACKGROUND", "EFFECT_COLOR", "ERROR_STRIPE_COLOR")


@dataclass
class Scheme:
    colors: dict[str, str | None] = field(default_factory=dict)
    attributes: dict[str, dict[str, str | None]] = field(default_factory=dict)


def scheme_color(value: str | None) -> str | None:
    if not value:
        return None
    number = int(value, 16)
    return f"#{number:08X}" if len(value) > 6 else f"#{number:06X}"


def _scheme_values(value) -> dict[str, str | None]:
    return {option.get("name"): option.get("value") for option in value}


def _children(element, tag: str) -> list:
    child = element.find(tag)
    return list(child) if child is not None else []


def _read_scheme(element) -> Scheme:
    scheme = Scheme()
    for option in _children(element, "colors"):
        scheme.colors[option.get("name")] = scheme_color(option.get("value"))
    for option in _children(element, "attributes"):
        value = option.find("value")
        if value is not None:
            scheme.attributes[option.get("name")] = _normalize_fields(_scheme_values(value))
        elif option.get("baseAttributes"):
            scheme.attributes[option.get("name")] = {"baseAttributes": option.get("baseAttributes")}
    return scheme


def _normalize_fields(fields: dict[str, str | None]) -> dict[str, str | None]:
    return {k: scheme_color(v) if k in COLOR_FIELDS else v for k, v in fields.items()}


def read_scheme_xml(text: str) -> Scheme:
    return _read_scheme(ET.fromstring(text))


def bundled_scheme(name: str) -> Scheme:
    """Default or Darcula as the IDE sees it, with plugin additions."""
    root = ET.parse(PARENT_DIR / "DefaultColorSchemesManager.xml").getroot()
    schemes = {element.get("name"): _read_scheme(element) for element in root.findall("scheme")}
    scheme = schemes["Default"]
    if name == "Darcula":
        scheme = Scheme(_merge(schemes["Darcula"].colors, scheme.colors), _merge(schemes["Darcula"].attributes, scheme.attributes))
    additions = json.loads((PARENT_DIR / "additional-attributes.json").read_text())[name]
    for key, fields in additions.items():
        scheme.attributes.setdefault(key, _normalize_fields(fields))
    return scheme


def effective_scheme(scheme: Scheme, parent: str) -> Scheme:
    base = bundled_scheme(parent)
    return Scheme(_merge(scheme.colors, base.colors), _merge(scheme.attributes, base.attributes))
