{
  description = "Kansō themes for JetBrains IDEs, generated from kanso.nvim";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    # The palette source. palette/kanso.json is exported from this revision; the
    # palette check fails when the two differ.
    kanso-nvim = {
      url = "github:webhooked/kanso.nvim/1afbbb449aa0254823dbe1932e3cbb51886ff9fe";
      flake = false;
    };
  };

  outputs = {
    self,
    nixpkgs,
    kanso-nvim,
  }: let
    systems = ["aarch64-darwin" "x86_64-darwin" "aarch64-linux" "x86_64-linux"];
    forAllSystems = f: nixpkgs.lib.genAttrs systems (system: f nixpkgs.legacyPackages.${system});
    version = "0.1.0";
  in {
    packages = forAllSystems (pkgs: {
      default = pkgs.stdenvNoCC.mkDerivation {
        pname = "kanso-jetbrains";
        inherit version;
        src = self;
        nativeBuildInputs = [pkgs.python3];
        buildPhase = ''
          runHook preBuild
          python3 -m kanso_jetbrains build --palette palette/kanso.json --version ${version} --out kanso-jetbrains-${version}.jar
          runHook postBuild
        '';
        installPhase = ''
          runHook preInstall
          install -Dm644 kanso-jetbrains-${version}.jar $out/kanso-jetbrains-${version}.jar
          runHook postInstall
        '';
        PYTHONPATH = "src";
      };
    });

    apps = forAllSystems (pkgs: {
      # Rewrites palette/kanso.json from the pinned kanso.nvim input.
      export-palette = {
        type = "app";
        program = nixpkgs.lib.getExe (pkgs.writeShellApplication {
          name = "export-palette";
          runtimeInputs = [pkgs.neovim pkgs.jq];
          text = ''
            nvim --headless -u NONE -l scripts/export-palette.lua ${kanso-nvim} | jq -S . > palette/kanso.json
          '';
        });
      };
      # JetBrains Plugin Verifier against an installed IDE:
      #   nix run .#verify -- "/Applications/IntelliJ IDEA.app/Contents"
      verify = {
        type = "app";
        program = nixpkgs.lib.getExe (pkgs.writeShellApplication {
          name = "verify";
          runtimeInputs = [pkgs.jdk21_headless];
          text = ''
            verifier=${pkgs.fetchurl {
              url = "https://github.com/JetBrains/intellij-plugin-verifier/releases/download/1.411/verifier-cli-1.411-all.jar";
              hash = "sha256-1swcHxd2G7Xv/xh/mLY/t5LH7yovuSArtdvqBevAK/o=";
            }}
            work=$(mktemp -d)
            trap 'rm -rf "$work"' EXIT
            # The verifier exits 0 even for an invalid plugin, so check its verdict.
            java -jar "$verifier" check-plugin ${self.packages.${pkgs.stdenv.hostPlatform.system}.default}/kanso-jetbrains-${version}.jar "$1" \
              -verification-reports-dir "$work/reports" -offline 2>&1 | tee "$work/log" | grep -v '^Layout component'
            grep -Eq '^Plugin .* against .*: Compatible$' "$work/log"
          '';
        });
      };
    });

    checks = forAllSystems (pkgs: {
      palette = pkgs.runCommand "kanso-palette-current" {nativeBuildInputs = [pkgs.neovim pkgs.jq];} ''
        export HOME=$TMPDIR
        nvim --headless -u NONE -l ${self}/scripts/export-palette.lua ${kanso-nvim} | jq -S . > exported.json
        if ! diff -u ${self}/palette/kanso.json exported.json; then
          echo "palette/kanso.json differs from kanso.nvim; run: nix run .#export-palette" >&2
          exit 1
        fi
        touch $out
      '';
      tests = pkgs.runCommand "kanso-jetbrains-tests" {nativeBuildInputs = [pkgs.python3];} ''
        cd ${self}
        PYTHONPATH=src python3 -m unittest discover -s tests -v
        touch $out
      '';
      plugin = self.packages.${pkgs.stdenv.hostPlatform.system}.default;
    });

    devShells = forAllSystems (pkgs: {
      default = pkgs.mkShell {packages = [pkgs.python3 pkgs.neovim pkgs.jq pkgs.alejandra];};
    });

    formatter = forAllSystems (pkgs: pkgs.alejandra);
  };
}
