class AniworldCli < Formula
  desc "CLI tool to browse and watch anime from aniworld.to"
  homepage "https://github.com/dxmoc/aniworld-cli"
  url "https://github.com/dxmoc/aniworld-cli/archive/refs/heads/main.tar.gz"
  version "1.0.0"
  sha256 ""
  license "GPL-3.0"

  depends_on "bash"
  depends_on "curl"
  depends_on "fzf"
  depends_on "grep"
  depends_on "node"
  depends_on "sed"

  def install
    bin.install "aniworld-cli"

    libexec.install Dir["lib/*"]

    inreplace bin/"aniworld-cli", 'LIB_DIR="${SCRIPT_DIR}/lib"', "LIB_DIR=\"#{libexec}\""

    doc.install "README.md"
  end

  def caveats
    <<~EOS
      aniworld-cli requires a video player for playback.
      Install mpv (recommended):
        brew install mpv

      Optional dependencies for enhanced functionality:
        brew install yt-dlp ffmpeg aria2
    EOS
  end

  test do
    assert_match "aniworld-cli", shell_output("#{bin}/aniworld-cli --help", 0)
  end
end
