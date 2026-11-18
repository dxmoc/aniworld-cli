# The aniworld-cli package a module should install: the Anime4K bundle with the
# requested mode when anime4k is enabled, the plain CLI otherwise.
#
# Shared by the Home Manager and NixOS modules so the two cannot drift apart.
{ self }:
{
  pkgs,
  enable ? true,
  mode ? "a",
  hq ? false,
}:
let
  packages = self.packages.${pkgs.stdenv.hostPlatform.system};
in
if enable then
  packages.aniworld-cli-anime4k.override {
    mpvAnime4k = packages.mpv-anime4k.override { inherit mode hq; };
  }
else
  packages.aniworld-cli
