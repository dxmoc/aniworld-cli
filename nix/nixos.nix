# NixOS system module: installs aniworld-cli system-wide, with the Anime4K mpv
# bundle when anime4k.enable is set.
#
#   programs.aniworld-cli = {
#     enable = true;
#     anime4k.enable = true;   # bundles an Anime4K-enabled mpv
#     anime4k.mode = "a";      # 1080p; "b" for 720p, "c" for 480p, ...
#   };
#
# This puts the CLI (and, with anime4k, the mpv wrapper it launches) in
# environment.systemPackages, so every user on the machine gets it. For a
# single user, use the Home Manager module instead; the option names match.
{ self }:
{
  config,
  lib,
  pkgs,
  ...
}:
let
  cfg = config.programs.aniworld-cli;
in
{
  options.programs.aniworld-cli = {
    enable = lib.mkEnableOption "aniworld-cli, a streaming-only CLI for aniworld.to";

    package = lib.mkOption {
      type = lib.types.package;
      default = (import ./cli-package.nix { inherit self; }) {
        inherit pkgs;
        enable = cfg.anime4k.enable;
        inherit (cfg.anime4k) mode hq;
      };
      defaultText = lib.literalExpression "aniworld-cli, or its Anime4K bundle when anime4k.enable is set";
      description = "The aniworld-cli package to install.";
    };

    anime4k = {
      enable = lib.mkEnableOption ''
        Anime4K v4 upscaling, bundled with an mpv wrapper (shaders from the Nix
        store, Ctrl+1..Ctrl+6 for the profiles and Ctrl+a for a menu, from the
        bundled mpv/aniworld-anime4k.lua; your input.conf is left alone)
      '';

      mode = lib.mkOption {
        type = lib.types.enum [
          "a"
          "b"
          "c"
          "a+a"
          "b+b"
          "c+a"
        ];
        default = "a";
        description = ''
          Starting Anime4K mode: "a" for 1080p, "b" for 720p, "c" for 480p, and
          the "a+a"/"b+b"/"c+a" variants for a sharper, more artifact-prone image.
        '';
      };

      hq = lib.mkOption {
        type = lib.types.bool;
        default = false;
        description = ''
          Use the larger (VL/M) CNN variants instead of the fast M/S ones. Slower;
          it needs a reasonably strong GPU to keep 24 fps.
        '';
      };
    };
  };

  config = lib.mkIf cfg.enable {
    environment.systemPackages = [ cfg.package ];
  };
}
