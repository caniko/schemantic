{
  description = "schemantic: Python uv project";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";

    py-harbor = {
      url = "git+https://codeberg.org/caniko/py-harbor.git";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    treefmt-nix.url = "github:numtide/treefmt-nix";
    git-hooks.url = "github:cachix/git-hooks.nix";
  };

  outputs = {
    self,
    nixpkgs,
    py-harbor,
    treefmt-nix,
    git-hooks,
    ...
  }:
    let
      py = py-harbor.lib;

      mkDevShells =
        system:
        let
          pkgs = py.mkPkgs { inherit system; };
          treefmtEval = treefmt-nix.lib.evalModule pkgs (import ./nix/treefmt.nix);
          pre-commit-check = git-hooks.lib.${system}.run {
            src = ./.;
            hooks = import ./nix/pre-commit.nix {
              inherit pkgs;
              treefmtWrapper = treefmtEval.config.build.wrapper;
            };
          };
        in
        {
          default = py.mkUvDevShell {
            inherit pkgs;
            uvExtra = "default";
            devGroup = "dev";
            extraPackages = pre-commit-check.enabledPackages;
            shellHookSuffix = pre-commit-check.shellHook;
          };
        };

      mkPythonPackage =
        system:
        let
          pkgs = py.mkPkgs { inherit system; };
          python = pkgs.python313;
        in
        py.mkUvAppPackage {
          inherit pkgs python;
          name = "schemantic-cpu";
          envName = "schemantic-cpu-env";
          workspaceRoot = ./.;
          dependencies = {
            schemantic = [ "default" ];
          };
          scripts = [
            "schemantic"
          ];
        };

      mkPythonCheckEnv =
        system:
        let
          pkgs = py.mkPkgs { inherit system; };
          python = pkgs.python313;
        in
        py.mkUvCheckEnv {
          inherit pkgs python;
          name = "schemantic-cpu-env-check";
          workspaceRoot = ./.;
          dependencies = {
            schemantic = [
              "default"
              "dev"
            ];
          };
        };

      mkChecks =
        system:
        let
          pkgs = py.mkPkgs { inherit system; };
          treefmtEval = treefmt-nix.lib.evalModule pkgs (import ./nix/treefmt.nix);
          checkEnv = mkPythonCheckEnv system;
          package = self.packages.${system}.schemantic-cpu;
        in
        {
          flake-eval = pkgs.runCommand "schemantic-flake-eval" { } ''
            test -x ${package}/bin/schemantic
            mkdir -p $out
            echo ok > $out/result
          '';
          formatting = treefmtEval.config.build.check self;
          offline-tests = pkgs.runCommand "schemantic-offline-tests" { } ''
            export HOME=$TMPDIR/home
            export XDG_CACHE_HOME=$TMPDIR/cache
            mkdir -p "$HOME" "$XDG_CACHE_HOME" "$out"
            cd ${./.}
            ${checkEnv}/bin/python -m pytest -p no:cacheprovider
            echo ok > $out/result
          '';
          typecheck = pkgs.runCommand "schemantic-typecheck" { } ''
            export HOME=$TMPDIR/home
            export XDG_CACHE_HOME=$TMPDIR/cache
            mkdir -p "$HOME" "$XDG_CACHE_HOME" "$out"
            cd ${./.}
            ${checkEnv}/bin/python -m mypy .
            echo ok > $out/result
          '';
          uv-format = pkgs.runCommand "schemantic-uv-format" { } ''
            export HOME=$TMPDIR/home
            export XDG_CACHE_HOME=$TMPDIR/cache
            export UV_NO_SYNC=1
            mkdir -p "$HOME" "$XDG_CACHE_HOME" "$out"
            cd ${./.}
            ${checkEnv}/bin/uv run --no-sync ruff format --check .
            echo ok > $out/result
          '';
        };

    in
    {
      devShells = py.forAllSystems mkDevShells;

      packages = py.forPackageSystems (
        system:
        let
          package = mkPythonPackage system;
        in
        {
          schemantic-cpu = package;
          default = package;
        }
      );

      apps = py.forPackageSystems (
        system:
        let
          package = self.packages.${system}.schemantic-cpu;
        in
        {
          schemantic-cpu = {
            type = "app";
            program = "${package}/bin/schemantic";
          };
          default = self.apps.${system}.schemantic-cpu;
        }
      );

      formatter = py.forAllSystems (
        system:
        let
          pkgs = py.mkPkgs { inherit system; };
          treefmtEval = treefmt-nix.lib.evalModule pkgs (import ./nix/treefmt.nix);
        in
        treefmtEval.config.build.wrapper
      );

      checks = py.forPackageSystems mkChecks;
    };
}
