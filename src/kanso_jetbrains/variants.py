"""The four Kansō variants and the colors that the JetBrains themes take from them.

Syntax, diagnostics, diff, VCS, and terminal colors are kanso.nvim's own theme
roles (palette/kanso.json). JetBrains also needs a few UI decisions that Neovim
does not make; they come from the palette and follow the Kansō VS Code themes
where those exist (accent badge color, light selection).
"""

import json
from dataclasses import dataclass
from pathlib import Path

from .color import normalize

# Four background steps per variant, from the editor background outwards.
SURFACES = {
    "zen": ("zenBg0", "zenBg1", "zenBg2", "zenBg3"),
    "ink": ("inkBg0", "inkBg1", "inkBg2", "inkBg3"),
    "mist": ("mistBg0", "mistBg1", "mistBg2", "mistBg3"),
    "pearl": ("pearlWhite0", "pearlWhite1", "pearlWhite2", "pearlWhite3"),
}

ORDER = ("zen", "ink", "mist", "pearl")


@dataclass(frozen=True)
class Variant:
    key: str
    palette: dict
    theme: dict

    @property
    def name(self) -> str:
        return f"Kanso {self.key.capitalize()}"

    @property
    def theme_id(self) -> str:
        return f"kanso-{self.key}"

    @property
    def dark(self) -> bool:
        return self.key != "pearl"

    @property
    def file_stem(self) -> str:
        return f"kanso_{self.key}"

    def ui(self, role: str) -> str:
        return self._role("ui", role)

    def syn(self, role: str) -> str:
        return self._role("syn", role)

    def diag(self, role: str) -> str:
        return self._role("diag", role)

    def diff(self, role: str) -> str:
        return self._role("diff", role)

    def vcs(self, role: str) -> str:
        return self._role("vcs", role)

    def term(self, index: int) -> str:
        return normalize(self.theme["term"][index])

    def color(self, name: str) -> str:
        return normalize(self.palette[name])

    def _role(self, group: str, role: str) -> str:
        value = self.theme[group]
        for part in role.split("."):
            value = value[part]
        return normalize(value)

    @property
    def surfaces(self) -> tuple[str, str, str, str]:
        return tuple(self.color(name) for name in SURFACES[self.key])

    @property
    def brand(self) -> str:
        """Accent for buttons, badges, toggles, and focus. Dark variants use the VS Code
        badge color; pearl's (pearlTeal3) is too light for text on it, so pearl uses
        its function blue."""
        return self.color("blue2" if self.dark else "pearlBlue4")

    @property
    def selection(self) -> str:
        """Selected text and rows. Pearl's visual background is too close to its
        cursor line in an IDE, so pearl uses the VS Code selection color."""
        return self.ui("bg_visual") if self.dark else self.color("pearlBlue1")

    @property
    def search(self) -> str:
        return self.ui("bg_search")


def load_variants(palette_path: Path) -> list[Variant]:
    data = json.loads(palette_path.read_text())
    return [Variant(key, data["palette"], data["themes"][key]) for key in ORDER]
