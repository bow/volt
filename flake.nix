{
  description = "Nix flake for Volt";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/9355fa86e6f27422963132c2c9aeedb0fb963d93";
    flake-utils.url = "github:numtide/flake-utils/b1d9ab70662946ef0850d488da1c9019f3a9752a";
    poetry2nix = {
      url = "github:bow/poetry2nix/feature/more-build-overrides";
      inputs.nixpkgs.follows = "nixpkgs";
      inputs.flake-utils.follows = "flake-utils";
    };
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
        pythonPkgs = pkgs.python312Packages;
        shellPkgs = with pkgs; [
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
          inherit python;
          projectDir = self;
          overrides = p2n.overrides.withDefaults (
            # Using wheel since mypy compilation is too long and it is only a dev/test dependency.
            _final: prev: { mypy = prev.mypy.override { preferWheel = true; }; }
          );
        };
      in
      {
        apps = {
          default = {
            type = "app";
            program = "${app}/bin/${app.pname}";
          };
        };
        devShells = {
          ci = pkgs.mkShellNoCC { packages = shellPkgs ++ [ app ]; };
          default = pkgs.mkShellNoCC rec {
            nativeBuildInputs = with pkgs; [
              python
              pythonPkgs.venvShellHook
              taglib
              openssl
              git
              libxml2
              libxslt
              libzip
              zlib
            ];
            packages = shellPkgs;
            venvDir = "./.venv";
            postVenvCreation = ''
              unset SOURCE_DATE_EPOCH
              poetry env use ${venvDir}/bin/python
              poetry install
            '';
            postShellHook = ''
              unset SOURCE_DATE_EPOCH
            '';
          };
        };
        packages =
          let
            imgTag = if app.version != "0.0.dev0" then app.version else "latest";
            imgAttrs = rec {
              name = "ghcr.io/bow/${app.pname}";
              tag = imgTag;
              contents = [ app ];
              config = {
                Entrypoint = [ "/bin/${app.pname}" ];
                Labels = {
                  "org.opencontainers.image.revision" =
                    with builtins;
                    let
                      revFile = "${self}/.rev";
                    in
                    if pathExists revFile then (readFile revFile) else "";
                  "org.opencontainers.image.source" = "https://github.com/bow/${app.pname}";
                  "org.opencontainers.image.title" = "${app.pname}";
                  "org.opencontainers.image.url" = "https://${name}";
                };
              };
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
