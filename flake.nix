{
  description = "Nix flake for Volt";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";

    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };

    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs = {
        pyproject-nix.follows = "pyproject-nix";
        uv2nix.follows = "uv2nix";
        nixpkgs.follows = "nixpkgs";
      };
    };
  };

  outputs =
    {
      self,
      nixpkgs,
      uv2nix,
      pyproject-nix,
      pyproject-build-systems,
      ...
    }:
    let
      inherit (nixpkgs) lib;

      supportedSystems = [
        "x86_64-linux"
        "x86_64-darwin"
        "aarch64-linux"
        "aarch64-darwin"
      ];

      forEachSupportedSystem =
        f:
        let
          bySystem = nixpkgs.lib.genAttrs supportedSystems f;

          transpose =
            systemAttrs:
            let
              getOrEmpty = attrs: key: if builtins.hasAttr key attrs then attrs.${key} else { };
              foldOp =
                acc: systemKey:
                let
                  value = systemAttrs.${systemKey};
                  mapOp = topKey: value: lib.recursiveUpdate (getOrEmpty acc topKey) { ${systemKey} = value; };
                in
                acc // (builtins.mapAttrs mapOp value);
              systemKeys = builtins.attrNames systemAttrs;
            in
            builtins.foldl' foldOp { } systemKeys;
        in
        transpose bySystem;
    in
    forEachSupportedSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python313;
        devPkgs = [
          python
          pkgs.black
          pkgs.deadnix
          pkgs.just
          pkgs.nixfmt-rfc-style
          pkgs.pre-commit
          pkgs.ruff
          pkgs.statix
          pkgs.uv
        ];
        ciPkgs = devPkgs ++ [ pkgs.skopeo ];

        workspace = uv2nix.lib.workspace.loadWorkspace { workspaceRoot = ./.; };
        overlay = workspace.mkPyprojectOverlay { sourcePreference = "wheel"; };
        pythonSet = (pkgs.callPackage pyproject-nix.build.packages { inherit python; }).overrideScope (
          nixpkgs.lib.composeManyExtensions [
            pyproject-build-systems.overlays.default
            overlay
          ]
        );
        venvCI = pythonSet.mkVirtualEnv "volt-env-ci" workspace.deps.all;
        venvRelease = pythonSet.mkVirtualEnv "volt-env-release" workspace.deps.optionals;
        app = (pkgs.callPackages pyproject-nix.build.util { }).mkApplication {
          venv = venvRelease;
          package = pythonSet.volt;
        };
      in
      {
        apps = {
          default = {
            type = "app";
            program = "${venvRelease}/bin/${app.pname}";
          };
        };
        devShells = {
          ci = pkgs.mkShellNoCC { packages = ciPkgs ++ [ venvCI ]; };
          default = pkgs.mkShell rec {
            nativeBuildInputs = [ python.pkgs.venvShellHook ];
            packages = devPkgs;
            env = {
              UV_PYTHON_DOWNLOADS = "never";
              UV_PYTHON = "${venvDir}/bin/python";
            };
            venvDir = "./.venv";
            postVenvCreation = ''
              unset SOURCE_DATE_EPOCH
              uv sync --all-groups --active --locked
              . ${venvDir}/bin/activate
            '';
            postShellHook = ''
              unset SOURCE_DATE_EPOCH
              unset PYTHONPATH
            '';
          };
        };
        formatter = pkgs.nixfmt-rfc-style;
        packages =
          let
            readFileOr = path: default: with builtins; if pathExists path then (readFile path) else default;
            imgTag = if app.version != "0.0.dev0" then app.version else "latest";
            imgAttrs = rec {
              name = "ghcr.io/bow/${app.pname}";
              tag = imgTag;
              contents = [ app ];
              config = {
                Entrypoint = [ "/bin/${app.pname}" ];
                Labels = {
                  "org.opencontainers.image.revision" = readFileOr "${self}/.rev" "";
                  "org.opencontainers.image.source" = "https://github.com/bow/${app.pname}";
                  "org.opencontainers.image.title" = "${app.pname}";
                  "org.opencontainers.image.url" = "https://${name}";
                };
              };
            };
          in
          {
            default = venvRelease;
            dockerArchive = pkgs.dockerTools.buildLayeredImage imgAttrs;
            dockerArchiveStreamer = pkgs.dockerTools.streamLayeredImage imgAttrs;
          };
      }
    );
}
