import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from helper.ffmpeg_tools import build_encode_command, build_metadata_command

FFMPEG = shutil.which("ffmpeg")
FFPROBE = shutil.which("ffprobe")


@unittest.skipUnless(FFMPEG and FFPROBE, "ffmpeg/ffprobe are not installed")
class FFmpegIntegrationTests(unittest.TestCase):
    def test_generate_encode_and_metadata_remux_sample(self):
        with tempfile.TemporaryDirectory(prefix="aniflix-test-") as tmp:
            source = str(Path(tmp) / "sample source.mkv")
            create = [
                FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
                "-f", "lavfi", "-i", "testsrc=size=640x360:rate=24",
                "-f", "lavfi", "-i", "sine=frequency=1000:sample_rate=44100",
                "-t", "1", "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                "-c:a", "aac", source,
            ]
            generated = subprocess.run(create, capture_output=True, text=True, timeout=60)
            if generated.returncode != 0 and "Unknown encoder 'libx264'" in generated.stderr:
                self.skipTest("Installed FFmpeg lacks the libx264 encoder")
            self.assertEqual(generated.returncode, 0, generated.stderr)

            for resolution in (480, 720, 1080):
                output = str(Path(tmp) / f"encoded-{resolution}.mkv")
                result = subprocess.run(
                    build_encode_command(source, output, resolution, {"title": "ANIFLIX test"}),
                    capture_output=True, text=True, timeout=90,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                probe = subprocess.run(
                    [FFPROBE, "-v", "error", "-show_entries", "stream=width,height", "-of", "json", output],
                    capture_output=True, text=True, timeout=20,
                )
                self.assertEqual(probe.returncode, 0, probe.stderr)
                streams = json.loads(probe.stdout)["streams"]
                video = next(stream for stream in streams if "width" in stream)
                self.assertEqual(video["width"], 640)
                self.assertEqual(video["height"], 360)  # cap resolution without upscaling

            metadata_output = str(Path(tmp) / "metadata output.mkv")
            result = subprocess.run(
                build_metadata_command(source, metadata_output, {"title": "ANIFLIX regression title"}),
                capture_output=True, text=True, timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            probe = subprocess.run(
                [FFPROBE, "-v", "error", "-show_entries", "format_tags=title", "-of", "json", metadata_output],
                capture_output=True, text=True, timeout=20,
            )
            self.assertEqual(probe.returncode, 0, probe.stderr)
            tags = json.loads(probe.stdout).get("format", {}).get("tags", {})
            self.assertTrue(any(value == "ANIFLIX regression title" for value in tags.values()), tags)


if __name__ == "__main__":
    unittest.main()
