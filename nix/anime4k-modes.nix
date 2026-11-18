# The Anime4K v4 shader chains, mirroring aniworld_cli/anime4k.py.
#
# A step is either a role ("clamp", "adp2", "adp4") or "role:variant", where the
# variant is the CNN size S < M < L < VL < UL. `hq` moves every CNN step up two
# sizes, exactly like --anime4k-hq does in the CLI.
{ lib }:
let
  roles = {
    clamp = "Restore/Anime4K_Clamp_Highlights.glsl";
    adp2 = "Upscale/Anime4K_AutoDownscalePre_x2.glsl";
    adp4 = "Upscale/Anime4K_AutoDownscalePre_x4.glsl";
    restore = v: "Restore/Anime4K_Restore_CNN_${v}.glsl";
    restore_soft = v: "Restore/Anime4K_Restore_CNN_Soft_${v}.glsl";
    upscale = v: "Upscale/Anime4K_Upscale_CNN_x2_${v}.glsl";
    upscale_denoise = v: "Upscale+Denoise/Anime4K_Upscale_Denoise_CNN_x2_${v}.glsl";
  };

  # Fast (low-end GPU) variants, as in the official templates.
  chains = {
    a = [
      "clamp"
      "restore:M"
      "upscale:M"
      "adp2"
      "adp4"
      "upscale:S"
    ];
    b = [
      "clamp"
      "restore_soft:M"
      "upscale:M"
      "adp2"
      "adp4"
      "upscale:S"
    ];
    c = [
      "clamp"
      "upscale_denoise:M"
      "adp2"
      "adp4"
      "upscale:S"
    ];
    "a+a" = [
      "clamp"
      "restore:M"
      "upscale:M"
      "restore:S"
      "adp2"
      "adp4"
      "upscale:S"
    ];
    "b+b" = [
      "clamp"
      "restore_soft:M"
      "upscale:M"
      "adp2"
      "adp4"
      "restore_soft:S"
      "upscale:S"
    ];
    "c+a" = [
      "clamp"
      "upscale_denoise:M"
      "adp2"
      "adp4"
      "restore:S"
      "upscale:S"
    ];
  };

  variants =
    hq:
    {
      S = if hq then "M" else "S";
      M = if hq then "VL" else "M";
      L = if hq then "UL" else "L";
    };

  expand =
    hq: step:
    let
      parts = lib.splitString ":" step;
      role = builtins.head parts;
      size = if parts == [ role ] then null else lib.last parts;
    in
    if role == "clamp" then
      roles.clamp
    else if role == "adp2" then
      roles.adp2
    else if role == "adp4" then
      roles.adp4
    else
      roles.${role} (variants hq).${size};
in
{
  inherit chains;
  modes = builtins.attrNames chains;

  # Relative shader paths for `mode`, in processing order.
  chain =
    { mode, hq ? false }:
    if chains ? ${mode} then
      map (expand hq) chains.${mode}
    else
      throw "Unknown Anime4K mode '${mode}'. Choose one of: ${
        lib.concatStringsSep ", " (builtins.attrNames chains)
      }.";
}
