{
  description = "High-performance Python Grepper Environment";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };

  outputs = {
    self,
    nixpkgs,
  }: let
    pkgs = nixpkgs.legacyPackages.x86_64-linux;
  in {
    devShells.x86_64-linux.default = pkgs.mkShell {
      buildInputs = with pkgs; [
        uv
        python314
        stdenv.cc.cc.lib
        zlib
      ];

      shellHook = ''
        export UV_PYTHON_PREFERENCE=system
        export LD_LIBRARY_PATH="${pkgs.lib.makeLibraryPath [pkgs.stdenv.cc.cc.lib pkgs.zlib]}:$LD_LIBRARY_PATH"
      '';
    };
  };
}
