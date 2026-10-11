import os
import subprocess
import sys
import unittest
from pathlib import Path


class ConfigurationValidationTests(unittest.TestCase):
    def test_non_positive_ffmpeg_timeout_is_rejected(self):
        repository = Path(__file__).resolve().parents[1]
        environment = os.environ.copy()
        environment["FFMPEG_TIMEOUT"] = "0"
        result = subprocess.run(
            [sys.executable, "-c", "import config"],
            cwd=repository,
            env=environment,
            capture_output=True,
            text=True,
            timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("FFMPEG_TIMEOUT must be a positive number", result.stderr)


if __name__ == "__main__":
    unittest.main()
