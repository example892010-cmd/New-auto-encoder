import asyncio
import io
import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

from helper.ffmpeg_tools import build_encode_command, build_metadata_command, probe_duration, run_process

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

            duration = asyncio.run(probe_duration(source))
            self.assertIsNotNone(duration)
            self.assertAlmostEqual(duration, 1.0, delta=0.15)

            for resolution in (480, 720, 1080):
                output = str(Path(tmp) / f"encoded-{resolution}.mkv")
                progress_values = []

                async def record_progress(seconds):
                    progress_values.append(seconds)

                code, stdout, stderr = asyncio.run(
                    run_process(
                        build_encode_command(source, output, resolution, {"title": "ANIFLIX test"}),
                        timeout=90,
                        progress_callback=record_progress,
                    )
                )
                self.assertEqual(code, 0, stderr)
                self.assertIn("progress=end", stdout)
                self.assertTrue(progress_values, f"No progress callback for {resolution}p")
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

    def test_encoding_excludes_attached_cover_art_and_preserves_scene_and_audio(self):
        with tempfile.TemporaryDirectory(prefix="aniflix-cover-test-") as tmp:
            cover = str(Path(tmp) / "cover.png")
            source = str(Path(tmp) / "source-with-cover.mp4")
            legacy_output = str(Path(tmp) / "legacy-all-streams.mkv")
            fixed_output = str(Path(tmp) / "primary-video-only.mkv")

            cover_result = subprocess.run(
                [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "lavfi",
                 "-i", "color=c=red:s=320x180", "-frames:v", "1", cover],
                capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(cover_result.returncode, 0, cover_result.stderr)

            create = [
                FFMPEG, "-hide_banner", "-loglevel", "error", "-y",
                "-loop", "1", "-framerate", "1", "-i", cover,
                "-f", "lavfi", "-i", "testsrc2=size=320x180:rate=24:duration=2",
                "-f", "lavfi", "-i", "sine=frequency=440:sample_rate=44100:duration=2",
                "-map", "0:v:0", "-map", "1:v:0", "-map", "2:a:0",
                "-c:v:0", "mjpeg", "-c:v:1", "libx264", "-pix_fmt:v:1", "yuv420p",
                "-c:a", "aac", "-t", "2", "-disposition:v:0", "attached_pic",
                "-disposition:v:1", "default", "-movflags", "+faststart", source,
            ]
            generated = subprocess.run(create, capture_output=True, text=True, timeout=60)
            self.assertEqual(generated.returncode, 0, generated.stderr)

            def probe(path):
                result = subprocess.run(
                    [FFPROBE, "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
                    capture_output=True, text=True, timeout=20,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                return json.loads(result.stdout)

            source_info = probe(source)
            source_video_streams = [s for s in source_info["streams"] if s["codec_type"] == "video"]
            self.assertEqual(len(source_video_streams), 2)
            self.assertTrue(any(s["disposition"].get("attached_pic") for s in source_video_streams))

            # Reproduce the previous `-map 0` behavior: the attached picture is
            # encoded as another video stream, leaving players a second visual track.
            legacy_command = [
                FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", source,
                "-map", "0", "-map_metadata", "0", "-vf", r"scale=-2:min(ih\,480)",
                "-c:v", "libx264", "-preset", "ultrafast", "-crf", "26",
                "-c:a", "copy", "-c:s", "copy", legacy_output,
            ]
            legacy = subprocess.run(legacy_command, capture_output=True, text=True, timeout=60)
            self.assertEqual(legacy.returncode, 0, legacy.stderr)
            self.assertEqual(
                sum(s["codec_type"] == "video" for s in probe(legacy_output)["streams"]), 2
            )

            code, _, stderr = asyncio.run(
                run_process(build_encode_command(source, fixed_output, 480), timeout=60)
            )
            self.assertEqual(code, 0, stderr)
            fixed_info = probe(fixed_output)
            fixed_videos = [s for s in fixed_info["streams"] if s["codec_type"] == "video"]
            self.assertEqual(len(fixed_videos), 1)
            self.assertFalse(fixed_videos[0]["disposition"].get("attached_pic"))

            source_audio = next(s for s in source_info["streams"] if s["codec_type"] == "audio")
            fixed_audio = next(s for s in fixed_info["streams"] if s["codec_type"] == "audio")
            self.assertEqual(fixed_audio["codec_name"], source_audio["codec_name"])
            self.assertAlmostEqual(float(fixed_audio["start_time"]), float(source_audio["start_time"]), delta=0.1)

            def frame_at(path, stream_specifier):
                result = subprocess.run(
                    [FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-i", path,
                     "-ss", "0.5", "-map", stream_specifier, "-frames:v", "1",
                     "-f", "image2pipe", "-c:v", "png", "pipe:1"],
                    capture_output=True, timeout=30,
                )
                self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))
                return Image.open(io.BytesIO(result.stdout)).convert("RGB")

            original_frame = frame_at(source, "0:V:0")
            encoded_frame = frame_at(fixed_output, "0:v:0")
            self.assertEqual(original_frame.size, encoded_frame.size)
            mean_absolute_difference = sum(
                ImageStat.Stat(ImageChops.difference(original_frame, encoded_frame)).mean
            ) / 3
            self.assertLess(mean_absolute_difference, 20.0)


if __name__ == "__main__":
    unittest.main()
