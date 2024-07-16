{
  description = "Nix flake for Volt";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixpkgs-unstable";
    flake-utils.url = "github:numtide/flake-utils/b1d9ab70662946ef0850d488da1c9019f3a9752a";
    poetry2nix.url = "github:bow/poetry2nix/feature/more-build-overrides";
  };

  outputs = { self, nixpkgs, flake-utils, poetry2nix }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        p2n = poetry2nix.lib.mkPoetry2Nix { pkgs = pkgs; };
      in
      {
        packages = {
          default = p2n.mkPoetryApplication { projectDir = self; };
        };
        devShells = {
          default = pkgs.mkShellNoCC {
            packages = [
              (p2n.mkPoetryEnv { projectDir = self; })
              pkgs.poetry
            ];
          };
        };
      }
    );
}
