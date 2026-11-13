"""Copy the editor color data that the generator and tests need from an IDE.

Usage: python3 scripts/extract-ide-schemes.py <IDE home> <output directory>

<IDE home> is the directory with lib/ and plugins/ (on macOS: the app's Contents).
It writes DefaultColorSchemesManager.xml (the bundled Default and Darcula schemes)
and additional-attributes.json: the attributes that bundled plugins add to those
schemes through additionalTextAttributes. Language plugins that set explicit
colors there would show their stock colors in a scheme based on Default or
Darcula, so the generator remaps them.
"""

import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

REGISTRATION = re.compile(r'<additionalTextAttributes\s+scheme="(Default|Darcula)"\s+file="([^"]+)"')


def main() -> None:
    home, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    jars = sorted([*home.glob("lib/**/*.jar"), *home.glob("plugins/**/*.jar")])
    index: dict[str, list[Path]] = {}
    registrations = []
    for jar in jars:
        try:
            archive = zipfile.ZipFile(jar)
        except zipfile.BadZipFile:
            continue
        with archive:
            for name in archive.namelist():
                if not name.endswith(".xml"):
                    continue
                index.setdefault(name, []).append(jar)
                if name == "DefaultColorSchemesManager.xml" and jar.parent == home / "lib":
                    (out / name).write_bytes(archive.read(name))
                text = archive.read(name).decode("utf-8", "ignore")
                if "additionalTextAttributes" in text:
                    registrations += [(m[1], m[2], jar) for m in REGISTRATION.finditer(text)]

    attributes: dict[str, dict] = {"Default": {}, "Darcula": {}}
    for scheme, file, registering_jar in registrations:
        name = file.lstrip("/")
        name = name if name.endswith(".xml") else name + ".xml"
        plugin_root = _plugin_root(registering_jar, home)
        candidates = sorted(index.get(name, []), key=lambda jar: not jar.is_relative_to(plugin_root))
        if not candidates:
            print(f"missing {name} for {registering_jar}", file=sys.stderr)
            continue
        with zipfile.ZipFile(candidates[0]) as archive:
            root = ET.fromstring(archive.read(name))
        for option in root.iter("option"):
            key, value = option.get("name"), option.find("value")
            if key and value is not None:
                attributes[scheme][key] = {o.get("name"): o.get("value") for o in value}
            elif key and option.get("baseAttributes"):
                attributes[scheme][key] = {"baseAttributes": option.get("baseAttributes")}
    (out / "additional-attributes.json").write_text(json.dumps(attributes, indent=1, sort_keys=True) + "\n")
    print({scheme: len(values) for scheme, values in attributes.items()})


def _plugin_root(jar: Path, home: Path) -> Path:
    relative = jar.relative_to(home)
    return home / relative.parts[0] / relative.parts[1] if relative.parts[0] == "plugins" else home / "lib"


if __name__ == "__main__":
    main()
