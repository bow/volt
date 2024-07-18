{
  description = "Nix flake for Volt";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/9355fa86e6f27422963132c2c9aeedb0fb963d93";
    flake-utils.url = "github:numtide/flake-utils/b1d9ab70662946ef0850d488da1c9019f3a9752a";
    poetry2nix.url = "github:bow/poetry2nix/feature/more-build-overrides";
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        pythonPackages = pkgs.python312Packages;
        p2n = poetry2nix.lib.mkPoetry2Nix { inherit pkgs; };
        curDir = builtins.getEnv "PWD";
      in
      {
        devShells = {
          default = pkgs.mkShellNoCC {
            packages = [
              (
                p2n.mkPoetryEnv {
                  projectDir = curDir;
                  python = pkgs.python312; # NOTE: Keep in-sync with pyproject.toml.
                  editablePackageSources = { volt = curDir; };
                  overrides = p2n.overrides.withDefaults (final: prev: {
                    mypy = prev.mypy.override { preferWheel = true; };
                  });
                }
              )
              pkgs.poetry
              pythonPackages.poetry-dynamic-versioning
            ];
            # Without this, changes made in main source is only reflected when running
            # commands from  the projectDir, not in any of its subdirectories.
            shellHook = ''
              PYTHONPATH=${curDir}:$PYTHONPATH
            '';
          };
        };
      }
    );
}
