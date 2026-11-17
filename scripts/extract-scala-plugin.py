"""Copy the editor color data of the Scala plugin, which the IDE does not bundle.

Usage: python3 scripts/extract-scala-plugin.py <plugin dir> <output directory>

<plugin dir> is the unpacked plugin: the Scala directory with lib/ inside the
Marketplace zip. It writes scala-plugin.json:

- version: the plugin version (plugin.xml);
- keys: every text attribute key that the plugin's highlighter creates (the
  String constant fields of DefaultHighlighter, its *_ID names); the schemes
  must set each of them;
- additions: the attributes that the plugin adds to Default and Darcula
  (additionalTextAttributes), as extract-ide-schemes.py reads them for bundled
  plugins.
"""

import importlib.util
import json
import re
import struct
import sys
import zipfile
from pathlib import Path

HIGHLIGHTER = "org/jetbrains/plugins/scala/highlighter/DefaultHighlighter.class"


def main() -> None:
    plugin, out = Path(sys.argv[1]), Path(sys.argv[2])
    out.mkdir(parents=True, exist_ok=True)
    keys = version = None
    for jar in sorted(plugin.glob("lib/**/*.jar")):
        with zipfile.ZipFile(jar) as archive:
            names = set(archive.namelist())
            if HIGHLIGHTER in names:
                keys = string_fields(archive.read(HIGHLIGHTER))
            if "META-INF/plugin.xml" in names:
                found = re.search(r"<version>([^<]+)</version>", archive.read("META-INF/plugin.xml").decode())
                version = found[1] if found else version
    if keys is None or version is None:
        sys.exit(f"{plugin} has no {HIGHLIGHTER} or plugin version")
    data = {"version": version, "keys": sorted(keys), "additions": _ide_extractor().additional_attributes(plugin)}
    (out / "scala-plugin.json").write_text(json.dumps(data, indent=1, sort_keys=True) + "\n")
    print({"version": version, "keys": len(keys)} | {scheme: len(v) for scheme, v in data["additions"].items()})


def string_fields(data: bytes) -> list[str]:
    """The values of a class file's String constant fields (ConstantValue attributes)."""
    count = struct.unpack_from(">H", data, 8)[0]
    utf8: dict[int, str] = {}
    strings: dict[int, int] = {}
    index, pos = 1, 10
    while index < count:
        tag = data[pos]
        if tag == 1:  # Utf8
            length = struct.unpack_from(">H", data, pos + 1)[0]
            utf8[index] = data[pos + 3 : pos + 3 + length].decode("utf-8", "replace")
            pos += 3 + length
        elif tag == 8:  # String
            strings[index] = struct.unpack_from(">H", data, pos + 1)[0]
            pos += 3
        elif tag in (7, 16, 19, 20):  # Class, MethodType, Module, Package
            pos += 3
        elif tag == 15:  # MethodHandle
            pos += 4
        elif tag in (3, 4, 9, 10, 11, 12, 17, 18):
            pos += 5
        elif tag in (5, 6):  # Long and Double take two slots.
            pos += 9
            index += 1
        else:
            raise ValueError(f"unknown constant pool tag {tag}")
        index += 1
    # access_flags, this_class, super_class, then the interfaces.
    interfaces = struct.unpack_from(">H", data, pos + 6)[0]
    pos += 8 + 2 * interfaces
    values = []
    fields = struct.unpack_from(">H", data, pos)[0]
    pos += 2
    for _ in range(fields):
        _, _, descriptor, attributes = struct.unpack_from(">HHHH", data, pos)
        pos += 8
        for _ in range(attributes):
            name, length = struct.unpack_from(">HI", data, pos)
            if utf8[name] == "ConstantValue" and utf8[descriptor] == "Ljava/lang/String;":
                values.append(utf8[strings[struct.unpack_from(">H", data, pos + 6)[0]]])
            pos += 6 + length
    return values


def _ide_extractor():
    path = Path(__file__).with_name("extract-ide-schemes.py")
    spec = importlib.util.spec_from_file_location("extract_ide_schemes", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


if __name__ == "__main__":
    main()
