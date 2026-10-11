import asyncio
import os
import unittest

from helper.ffmpeg_tools import (
    MediaProcessingCancelled,
    build_encode_command,
    build_metadata_command,
    metadata_arguments,
    run_process,
)
from helper.filename import parse_filename, render_template, sanitize_filename
from helper.progress import ProgressReporter, format_bytes, format_eta


class FilenameTests(unittest.TestCase):
    def test_sxxexx_and_quality(self):
        self.assertEqual(
            parse_filename("Naruto Shippuden S01E01 1080p.mkv"),
            {"title": "Naruto Shippuden", "season": "01", "episode": "01", "quality": "1080p"},
        )

    def test_season_episode_spacing_and_case(self):
        parsed = parse_filename("[Example Show] S2 EP9 720p WEB-DL.mkv")
        self.assertEqual(parsed["season"], "02")
        self.assertEqual(parsed["episode"], "09")
        self.assertEqual(parsed["title"], "Example Show")
        self.assertEqual(parsed["quality"], "720p")

    def test_dotted_names_and_2160p(self):
        parsed = parse_filename("Series.S03.EP12.2160p.mkv")
        self.assertEqual((parsed["title"], parsed["season"], parsed["episode"], parsed["quality"]),
                         ("Series", "03", "12", "2160p"))

    def test_legacy_episode_and_unknown_quality(self):
        parsed = parse_filename("Movie - 7 - final.mkv")
        self.assertEqual(parsed["episode"], "07")
        self.assertEqual(parsed["quality"], "Unknown")

    def test_template_replacement_and_sanitization(self):
        name = render_template("{title} S{season} EP{episode} [{quality}]", "Show S1E2 1080p.mkv")
        self.assertEqual(name, "Show S01 EP02 [1080p]")
        unsafe = sanitize_filename("../../a/b\\c:bad?.mkv")
        self.assertNotIn("/", unsafe)
        self.assertNotIn("\\", unsafe)
        self.assertFalse(unsafe.startswith("."))


class FFmpegArgumentTests(unittest.TestCase):
    def test_metadata_args_are_flat_flag_value_pairs(self):
        args = metadata_arguments({"title": "A title", "author": "An author", "video": "Main video"})
        self.assertEqual(args, ["-metadata", "title=A title", "-metadata", "author=An author",
                                "-metadata:s:v", "title=Main video"])
        self.assertEqual(len(args) % 2, 0)

    def test_encode_command_limits_profiles_and_preserves_spaces(self):
        cmd = build_encode_command("/tmp/input name.mkv", "/tmp/output name.mkv", 720,
                                   {"title": "ANIFLIX encode"})
        self.assertIn("/tmp/input name.mkv", cmd)
        self.assertIn("libx264", cmd)
        self.assertIn("-vf", cmd)
        with self.assertRaises(ValueError):
            build_encode_command("in.mkv", "out.mkv", 360)

    def test_metadata_command_does_not_use_a_shell(self):
        cmd = build_metadata_command("source file.mkv", "output file.mkv", {"title": "A title"})
        self.assertEqual(cmd[0], "ffmpeg")
        self.assertIn("source file.mkv", cmd)
        self.assertIn("title=A title", cmd)


class ProcessCancellationTests(unittest.IsolatedAsyncioTestCase):
    async def test_process_timeout_terminates_subprocess(self):
        with self.assertRaises(TimeoutError):
            await run_process(
                [os.sys.executable, "-c", "import time; time.sleep(30)"],
                timeout=0.1,
            )

    async def test_process_cancellation_terminates_subprocess(self):
        event = asyncio.Event()
        async def cancel_soon():
            await asyncio.sleep(0.15)
            event.set()
        task = asyncio.create_task(cancel_soon())
        with self.assertRaises(MediaProcessingCancelled):
            await run_process(
                [os.sys.executable, "-c", "import time; time.sleep(30)"],
                timeout=5,
                cancel_event=event,
            )
        await task

    async def test_ffmpeg_progress_pipe_is_parsed_as_seconds(self):
        seen = []

        async def collect(seconds):
            seen.append(seconds)

        code, stdout, _ = await run_process(
            [
                os.sys.executable,
                "-c",
                "print('frame=1'); print('out_time=00:00:02.500000'); print('progress=continue')",
            ],
            timeout=5,
            progress_callback=collect,
        )
        self.assertEqual(code, 0)
        self.assertIn("progress=continue", stdout)
        self.assertEqual(seen, [2.5])


class ProgressReporterTests(unittest.IsolatedAsyncioTestCase):
    async def test_transfer_progress_matches_requested_bar_style(self):
        class FakeStatus:
            def __init__(self):
                self.texts = []

            async def edit_text(self, text):
                self.texts.append(text)

        status = FakeStatus()
        reporter = ProgressReporter(status, "Upload Started...", min_interval=0)
        await reporter.begin_transfer(1024)
        await reporter.transfer(512, 1024, force=True)
        text = status.texts[-1]
        self.assertIn("Upload Started...", text)
        self.assertIn("⬢" * 10 + "⬡" * 10, text)
        self.assertIn("Sɪᴢᴇ: 512.00 B | 1.00 KB", text)
        self.assertIn("Dᴏɴᴇ : 50.0%", text)
        self.assertIn("⏰️ ETA:", text)
        self.assertEqual(format_bytes(1024), "1.00 KB")
        self.assertEqual(format_eta(198), "3m, 18s")


if __name__ == "__main__":
    unittest.main()
