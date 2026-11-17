#!/usr/bin/env bash
# Refresh intellij/<build>/ for another IDE build.
#
#   scripts/update-intellij.sh <build> <IDE home>
#
# <build> is the IDE build number, for example 263.7307.200 (Help > About).
# <IDE home> is the installed IDE of that build (on macOS: "IntelliJ IDEA.app/Contents").
# Then set BUILD in src/kanso_jetbrains/intellij.py and run the tests.
set -euo pipefail
build=$1
home=$2
out="intellij/$build"
mkdir -p "$out"
base="https://raw.githubusercontent.com/JetBrains/intellij-community/idea/$build/platform/platform-resources/src/themes"
for theme in islands/ManyIslandsDark islands/ManyIslandsLight expUI/expUI_dark expUI/expUI_light \
  expUI/expUI_light_with_light_header intellijlaf darcula; do
  curl -fsSL "$base/$theme.theme.json" -o "$out/$(basename "$theme").theme.json"
done
python3 scripts/extract-ide-schemes.py "$home" "$out"
# The Scala plugin is not bundled: take its Marketplace release for this build.
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT
curl -fsSL "https://plugins.jetbrains.com/pluginManager?action=download&id=org.intellij.scala&build=IU-$build" -o "$work/scala.zip"
unzip -q "$work/scala.zip" -d "$work"
python3 scripts/extract-scala-plugin.py "$work/Scala" "$out"
