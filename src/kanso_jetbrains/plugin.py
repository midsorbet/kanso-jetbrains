"""plugin.xml and the plugin jar."""

import json
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape

from .editor_scheme import editor_scheme
from .ui_theme import ui_theme
from .variants import Variant

PLUGIN_ID = "io.github.midsorbet.kanso"
# Islands themes, which these themes extend, exist from 2025.3 (build 253).
SINCE_BUILD = "253"

DESCRIPTION = """\
<p>Kanso themes for JetBrains IDEs: the Zen, Ink, and Mist dark themes and the Pearl light theme,
generated from <a href="https://github.com/webhooked/kanso.nvim">kanso.nvim</a>.</p>
<p>Each theme extends the Islands theme of the same brightness and sets a matching editor color scheme.
The syntax colors follow kanso.nvim's highlight groups; comments and keywords are italic, as in kanso.nvim.</p>
<p><b>This plugin is entirely vibecoded:</b> an LLM wrote all of it, and nobody has reviewed the code line by line.</p>
"""


def plugin_xml(version: str, variants: list[Variant]) -> str:
    providers = "\n".join(
        f'    <themeProvider id="{v.theme_id}" path="/themes/{v.file_stem}.theme.json"/>' for v in variants
    )
    return f"""<idea-plugin>
  <id>{PLUGIN_ID}</id>
  <name>Kanso Theme</name>
  <version>{escape(version)}</version>
  <vendor url="https://github.com/midsorbet">midsorbet</vendor>
  <description><![CDATA[{DESCRIPTION}]]></description>
  <idea-version since-build="{SINCE_BUILD}"/>
  <depends>com.intellij.modules.platform</depends>
  <extensions defaultExtensionNs="com.intellij">
{providers}
  </extensions>
</idea-plugin>
"""


def plugin_files(version: str, variants: list[Variant]) -> dict[str, str]:
    files = {"META-INF/plugin.xml": plugin_xml(version, variants)}
    for v in variants:
        files[f"themes/{v.file_stem}.theme.json"] = json.dumps(ui_theme(v), indent=2) + "\n"
        files[f"schemes/{v.file_stem}.xml"] = editor_scheme(v)
    return files


def write_jar(path: Path, files: dict[str, str]) -> None:
    """A reproducible jar: sorted entries with a fixed timestamp."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as jar:
        entries = {"META-INF/MANIFEST.MF": "Manifest-Version: 1.0\r\n\r\n", **files}
        for name in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            jar.writestr(info, entries[name])
