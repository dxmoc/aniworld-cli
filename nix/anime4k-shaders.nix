# Anime4K v4.0.1 GLSL shaders, pinned by content hash.
#
# Only the files the six official modes use are fetched, so the closure stays
# small and nothing has to be downloaded while an episode plays. Same version
# the CLI's --anime4k downloader uses.
{
  lib,
  stdenvNoCC,
  fetchurl,
}:
let
  version = "v4.0.1";
  base = "https://raw.githubusercontent.com/bloc97/Anime4K/${version}/glsl";

  fetch =
    path: sha256:
    fetchurl {
      url = "${base}/${path}";
      inherit sha256;
    };

  shaderFiles = {
    "Restore/Anime4K_Clamp_Highlights.glsl" = fetch "Restore/Anime4K_Clamp_Highlights.glsl" "sha256-oqm/f7wdddCWYMoucB5Nf7DPVFe5TaR+GCUDL6KzZxo=";
    "Restore/Anime4K_Restore_CNN_M.glsl" = fetch "Restore/Anime4K_Restore_CNN_M.glsl" "sha256-Z+o+0mU56N47fTB2iFNdL/F+jRR+Ed2gJH2ndw2+z0E=";
    "Restore/Anime4K_Restore_CNN_S.glsl" = fetch "Restore/Anime4K_Restore_CNN_S.glsl" "sha256-l8JNw3CrMAwQi/qgnbfxda7/NDZ0hCwpnPOUCj0zBCc=";
    "Restore/Anime4K_Restore_CNN_VL.glsl" = fetch "Restore/Anime4K_Restore_CNN_VL.glsl" "sha256-NQNnInMzBc1NTldmC4g7viVpuikUAzwlQycQfXt3414=";
    "Restore/Anime4K_Restore_CNN_Soft_M.glsl" = fetch "Restore/Anime4K_Restore_CNN_Soft_M.glsl" "sha256-p4osdomOCOCeRCqWKMZCCMJujhV4lkm4dVIj8Al5TAI=";
    "Restore/Anime4K_Restore_CNN_Soft_S.glsl" = fetch "Restore/Anime4K_Restore_CNN_Soft_S.glsl" "sha256-n2hn8u9CeGcpUi2G/iQUfLTqFFQY45dN9wSWrPUtw5I=";
    "Restore/Anime4K_Restore_CNN_Soft_VL.glsl" = fetch "Restore/Anime4K_Restore_CNN_Soft_VL.glsl" "sha256-CUM0sOIMGiAf5JQcfGjeckUeWu6e+1Uk1/uCsS3KZLk=";
    "Upscale/Anime4K_AutoDownscalePre_x2.glsl" = fetch "Upscale/Anime4K_AutoDownscalePre_x2.glsl" "sha256-jFgpF0AUa9dmpNc/Eyd1p5f+gPfQeRm112fiel3IVlY=";
    "Upscale/Anime4K_AutoDownscalePre_x4.glsl" = fetch "Upscale/Anime4K_AutoDownscalePre_x4.glsl" "sha256-WvYtjNhEkW3BEmYT4TutO+qxlXh/k6cSALR8bsePLkE=";
    "Upscale/Anime4K_Upscale_CNN_x2_M.glsl" = fetch "Upscale/Anime4K_Upscale_CNN_x2_M.glsl" "sha256-cW4CCYpo8NZIdh8rlrTdE54csJsXS7Np/KOqNDKP/34=";
    "Upscale/Anime4K_Upscale_CNN_x2_S.glsl" = fetch "Upscale/Anime4K_Upscale_CNN_x2_S.glsl" "sha256-TFPsLih5CPfue8smawFwQhYm1mNXZGi319r8YpYmSaQ=";
    "Upscale/Anime4K_Upscale_CNN_x2_VL.glsl" = fetch "Upscale/Anime4K_Upscale_CNN_x2_VL.glsl" "sha256-Vjj+McN8FRo0Q/6jRRo++Rrwc/TbuWFfbA0eKdsRST0=";
    "Upscale+Denoise/Anime4K_Upscale_Denoise_CNN_x2_M.glsl" = fetch "Upscale+Denoise/Anime4K_Upscale_Denoise_CNN_x2_M.glsl" "sha256-jHKwQuIwH+ZqRcMIlyBFkUjiUEzXKvFvnA1QF/8UGB4=";
    "Upscale+Denoise/Anime4K_Upscale_Denoise_CNN_x2_VL.glsl" = fetch "Upscale+Denoise/Anime4K_Upscale_Denoise_CNN_x2_VL.glsl" "sha256-NZxI/loxf7xrcGzjaEAe70luhO2Yq6x6Q+/ryitl15s=";
  };
in
stdenvNoCC.mkDerivation {
  pname = "anime4k-shaders";
  inherit version;

  dontUnpack = true;
  dontBuild = true;

  installPhase = ''
    runHook preInstall
    ${lib.concatStrings (
      lib.mapAttrsToList (
        path: src: ''
          install -Dm644 ${src} "$out/share/anime4k/shaders/${path}"
        ''
      ) shaderFiles
    )}
    runHook postInstall
  '';

  meta = {
    description = "Anime4K ${version} GLSL shaders for mpv";
    homepage = "https://github.com/bloc97/Anime4K";
    license = lib.licenses.mit;
    platforms = lib.platforms.all;
  };
}
