# kanso-jetbrains

Generator for Kansō JetBrains themes. README.md explains the design.

- Change colors in `src/kanso_jetbrains/`, never in generated output. Write the
  generated files for review with
  `PYTHONPATH=src python3 -m kanso_jetbrains files --palette palette/kanso.json --version 0.0.0 --out build/files`.
- `palette/kanso.json` and `intellij/` are inputs copied from upstream; refresh
  them with `nix run .#export-palette` and `scripts/update-intellij.sh`, not by hand.
- Verify with `nix flake check` (palette, tests, plugin build). Run
  `nix run .#verify -- <IDE home>` when the descriptor or the IDE build changes.
- Prefer a test against the merged theme (`kanso_jetbrains.intellij`) to a
  screenshot. A visual check is for taste only.
- Nix ignores untracked files: `git add` new files before a Nix build.
