"""Build the plugin jar, or write the generated files to a directory for review.

    python -m kanso_jetbrains build --palette palette/kanso.json --version 0.1.0 --out kanso.jar
    python -m kanso_jetbrains files --palette palette/kanso.json --version 0.1.0 --out build/files
"""

import argparse
from pathlib import Path

from .plugin import plugin_files, write_jar
from .variants import load_variants


def main() -> None:
    parser = argparse.ArgumentParser(prog="kanso_jetbrains")
    parser.add_argument("command", choices=["build", "files"])
    parser.add_argument("--palette", type=Path, required=True)
    parser.add_argument("--version", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()

    files = plugin_files(args.version, load_variants(args.palette))
    if args.command == "build":
        write_jar(args.out, files)
    else:
        for name, text in files.items():
            target = args.out / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text)


if __name__ == "__main__":
    main()
