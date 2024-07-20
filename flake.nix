{
  description = "Nix flake for Volt";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/9355fa86e6f27422963132c2c9aeedb0fb963d93";
    flake-utils.url = "github:numtide/flake-utils/b1d9ab70662946ef0850d488da1c9019f3a9752a";
    poetry2nix.url = "github:bow/poetry2nix/feature/more-build-overrides";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      poetry2nix,
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        p2n = poetry2nix.lib.mkPoetry2Nix { inherit pkgs; };
        python = pkgs.python312; # NOTE: Keep in-sync with pyproject.toml.
        pythonPackages = pkgs.python312Packages;
        # Using wheel since mypy compilation is too long and it is only a dev/test dependency.
        overrides = p2n.overrides.withDefaults (
          _final: prev: { mypy = prev.mypy.override { preferWheel = true; }; }
        );
      in
      {
        packages =
          let
            app = p2n.mkPoetryApplication {
              inherit overrides python;
              projectDir = self;
            };
            imgTag = if app.version != "0.0.dev0" then app.version else "latest";
          in
          {
            default = app;
            dockerArchive = pkgs.dockerTools.buildImage {
              name = "ghcr.io/bow/${app.pname}";
              tag = imgTag;
              copyToRoot = [ app ];
              config.Entrypoint = [ "/bin/${app.pname}" ];
            };
          };
        devShells =
          let
            curDir = builtins.getEnv "PWD";
            poetry = pkgs.poetry.withPlugins (_ps: [ pythonPackages.poetry-dynamic-versioning ]);
            devEnv = p2n.mkPoetryEnv {
              inherit overrides python;
              projectDir = curDir;
              editablePackageSources = {
                volt = curDir;
              };
            };
          in
          {
            default = pkgs.mkShellNoCC {
              packages = [
                devEnv
                poetry
                pkgs.nixfmt-rfc-style
                pkgs.deadnix
                pkgs.statix
              ];
              # Without this, changes made in main source is only reflected when running
              # commands from  the projectDir, not in any of its subdirectories.
              shellHook = ''
                export PYTHONPATH=${curDir}:$PYTHONPATH
              '';
            };
          };
      }
    );
}
