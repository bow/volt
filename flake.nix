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
        overrides = p2n.overrides.withDefaults (
          # Using wheel since mypy compilation is too long and it is only a dev/test dependency.
          _final: prev: { mypy = prev.mypy.override { preferWheel = true; }; }
        );
        python = pkgs.python312; # NOTE: Keep in-sync with pyproject.toml.
        pythonPkgs = pkgs.python312Packages;
        pythonEnv = p2n.mkPoetryEnv rec {
          inherit overrides python;
          projectDir = self;
          editablePackageSources = {
            volt = projectDir;
          };
        };
        shellPkgs = with pkgs; [
          pythonEnv
          curl
          deadnix
          entr
          gnugrep
          nixfmt-rfc-style
          pre-commit
          skopeo
          statix
          (poetry.withPlugins (_ps: [ pythonPkgs.poetry-dynamic-versioning ]))
        ];
        app = p2n.mkPoetryApplication {
          inherit overrides python;
          projectDir = self;
        };
      in
      {
        apps = {
          default = {
            type = "app";
            program = "${app}/bin/${app.pname}";
          };
        };
        devShells = rec {
          ci = pkgs.mkShellNoCC { packages = shellPkgs; };
          default = ci.overrideAttrs (
            _final: prev: {
              # Set PYTHONPATH so that changes made in source tree is reflected from
              # wherever we are running commands, not just when we are in source root.
              shellHook =
                prev.shellHook
                + ''
                  export PYTHONPATH=${builtins.getEnv "PWD"}:$PYTHONPATH
                '';
            }
          );
        };
        packages =
          let
            imgTag = if app.version != "0.0.dev0" then app.version else "latest";
            imgAttrs = {
              name = "ghcr.io/bow/${app.pname}";
              tag = imgTag;
              contents = [ app ];
              config.Entrypoint = [ "/bin/${app.pname}" ];
            };
          in
          {
            default = app;
            dockerArchive = pkgs.dockerTools.buildLayeredImage imgAttrs;
            dockerArchiveStreamer = pkgs.dockerTools.streamLayeredImage imgAttrs;
          };
      }
    );
}
