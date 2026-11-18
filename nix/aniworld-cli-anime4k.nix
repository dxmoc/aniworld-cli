# aniworld-cli with the Anime4K-enabled mpv first on its PATH.
#
# ANIWORLD_ANIME4K=off keeps the CLI from downloading shaders (or appending a
# second chain): the mpv wrapper already carries them. `mpv` still wins over the
# plain mpv the CLI wrapper appends, because both use --suffix PATH.
{
  lib,
  pkgs,
  aniworld-cli,
  mpvAnime4k,
}:
pkgs.symlinkJoin {
  name = "aniworld-cli-anime4k";

  paths = [ aniworld-cli ];
  buildInputs = [ pkgs.makeWrapper ];

  postBuild = ''
    wrapProgram $out/bin/aniworld-cli \
      --suffix PATH : ${lib.makeBinPath [ mpvAnime4k ]} \
      --set ANIWORLD_ANIME4K off
  '';

  meta = (aniworld-cli.meta or { }) // {
    description = "aniworld-cli bundled with an Anime4K-enabled mpv (no runtime download)";
  };
}
