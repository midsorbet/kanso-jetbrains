# Kansō for JetBrains IDEs

> [!WARNING]
> **This project is entirely vibecoded.**
>
> An LLM (Anthropic Claude, through the OMP coding agent) wrote all of the
> code, tests, and documentation. The owner only steered it and looked at the
> result in an IDE. Nobody has reviewed the code line by line. The tests check
> the named properties and nothing more. Use it at your own risk; see
> [LICENSE](LICENSE) for the provenance record and the LLM disclaimer.

UI themes and editor color schemes for IntelliJ-based IDEs, generated from
[kanso.nvim](https://github.com/webhooked/kanso.nvim):

| Theme | Kind | Editor scheme |
| --- | --- | --- |
| Kanso Zen | dark, darkest | Kanso Zen |
| Kanso Ink | dark | Kanso Ink |
| Kanso Mist | dark, lightest | Kanso Mist |
| Kanso Pearl | light | Kanso Pearl |

Each theme extends the Islands theme of the same brightness (IntelliJ 2025.3
and later) and selects its editor scheme.

## Install

```sh
nix build
```

`result/kanso-jetbrains-<version>.jar` is the plugin. In the IDE, choose
Settings > Plugins > gear icon > Install Plugin from Disk, then pick a theme
under Settings > Appearance & Behavior > Appearance.

## How the colors are made

- `palette/kanso.json` is exported from kanso.nvim with Neovim
  (`nix run .#export-palette`). It holds the palette and kanso.nvim's resolved
  roles for each variant: `ui`, `syn`, `diag`, `diff`, `vcs`, and `term`. The
  `palette` flake check fails when the file differs from the pinned kanso.nvim.
- `src/kanso_jetbrains/ui_theme.py` redefines the named colors and color ramps
  that the Islands themes paint with. Parent keys that use a literal color get
  the Kansō value of the closest ramp color. Text that would fall below 4.5:1 on
  its background is moved toward Kansō's lightest or darkest color.
- `src/kanso_jetbrains/editor_scheme.py` maps kanso.nvim's highlight groups to
  IntelliJ attributes. Entries of the parent scheme (Default or Darcula, with
  the attributes that bundled plugins add) that the mapping does not cover
  inherit the matching `DEFAULT_*` attribute or get remapped colors. Code below
  3:1 is moved the same way; in Pearl this darkens the orange warning color.
- A few UI choices are not in kanso.nvim: the accent color (the VS Code badge
  color for the dark variants, Pearl's function blue for Pearl), Pearl's
  selection color (the VS Code selection color), and tighter spacing in
  compact density (2 px between islands instead of 4, 10 px corners instead
  of 16).

## Tests

```sh
nix flake check
```

The tests do not open an IDE. `src/kanso_jetbrains/intellij.py` follows the
IDE's theme loading code (`UIThemeBean.kt`, `UITheme.kt`): it merges a theme
over its parent chain and resolves the color names. `intellij/<build>/` holds
the parent themes and schemes of the pinned IDE build. The tests check that,
after the merge:

- no stock JetBrains color remains in the UI or the editor;
- every foreground has 4.5:1 against its background in the UI and 3:1 in the
  editor (the ANSI color slots are exempt);
- every color name resolves (IntelliJ makes an unknown name transparent);
- the jar contains every file that `plugin.xml` and the themes reference.

JetBrains' Plugin Verifier checks the plugin against an installed IDE:

```sh
nix run .#verify -- "/Applications/IntelliJ IDEA.app/Contents"
```

Look at the themes in the IDE once after a change to the color choices; the
tests cover correctness, not taste.

## Updating

- kanso.nvim: change the `kanso-nvim` input revision, run
  `nix run .#export-palette`, and review the palette diff.
- IDE build: run `scripts/update-intellij.sh <build> <IDE home>` with that
  build installed, set `BUILD` in `src/kanso_jetbrains/intellij.py`, and run the
  tests. New parent keys show up as test failures if they are not covered.

## License

Original project material is licensed under **`MIT OR LicenseRef-VIBE-1.0`**,
at your choice. See [LICENSE](LICENSE) and the full texts in
[LICENSES](LICENSES). Choosing MIT does not require VIBE's
modification-provenance disclosure. VIBE is not OSI-approved and has no SPDX
License List identifier.

The colors come from kanso.nvim (MIT). The files in `intellij/` are copied from
JetBrains IntelliJ IDEA (Apache-2.0); see `intellij/NOTICE`.
