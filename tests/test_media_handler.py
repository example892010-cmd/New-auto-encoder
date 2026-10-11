import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

os.environ.setdefault("DB_URL", "mongodb://127.0.0.1:27017")

from helper.database import AshutoshGoswami24
from helper.job_control import ACTIVE_JOBS
from plugins.file_rename import auto_rename_files


class FakeStatus:
    def __init__(self):
        self.texts = []

    async def edit(self, text):
        self.texts.append(text)
        return self


class FakeMessage:
    def __init__(self):
        self.from_user = SimpleNamespace(id=321, first_name="Tester")
        self.chat = SimpleNamespace(id=321)
        self.document = SimpleNamespace(
            file_id="mock-file-id",
            file_name="Series S01E02 1080p.mkv",
            file_size=12,
            mime_type="video/x-matroska",
        )
        self.video = None
        self.audio = None
        self.status = FakeStatus()

    async def reply_text(self, text):
        self.status.texts.append(text)
        return self.status


class FakeClient:
    def __init__(self, source):
        self.source = source
        self.sent = []
        self.temporary_dirs = []

    async def download_media(self, message_or_id, file_name=None):
        if not file_name:
            return None
        self.temporary_dirs.append(os.path.dirname(file_name))
        with open(file_name, "wb") as out:
            out.write(self.source)
        return file_name

    async def send_document(self, chat_id, document, caption, thumb=None, file_name=None):
        self.sent.append({
            "chat_id": chat_id,
            "path": document,
            "filename": file_name or os.path.basename(document),
            "local_basename": os.path.basename(document),
            "caption": caption,
            "exists_during_upload": os.path.isfile(document),
            "thumb": thumb,
        })


class MediaHandlerTests(unittest.IsolatedAsyncioTestCase):
    async def test_rename_caption_upload_and_temp_cleanup_with_mocks(self):
        message = FakeMessage()
        client = FakeClient(b"sample-media-data")
        ACTIVE_JOBS.clear()
        with (
            patch.object(AshutoshGoswami24, "get_format_template", new=AsyncMock(return_value="{title} S{season} EP{episode} [{quality}]")),
            patch.object(AshutoshGoswami24, "get_media_preference", new=AsyncMock(return_value="document")),
            patch.object(AshutoshGoswami24, "get_metadata", new=AsyncMock(return_value=False)),
            patch.object(AshutoshGoswami24, "get_thumbnail", new=AsyncMock(return_value=None)),
            patch.object(AshutoshGoswami24, "get_caption", new=AsyncMock(return_value="File: {filename} | {filesize} | {duration}")),
        ):
            await auto_rename_files(client, message)

        self.assertEqual(len(client.sent), 1)
        sent = client.sent[0]
        self.assertTrue(sent["exists_during_upload"])
        self.assertEqual(sent["filename"], "Series S01 EP02 [1080p].mkv")
        self.assertIn(sent["filename"], sent["caption"])
        self.assertEqual(sent["chat_id"], 321)
        self.assertEqual(ACTIVE_JOBS, {})
        self.assertTrue(all(not os.path.exists(path) for path in client.temporary_dirs))
        self.assertEqual(message.status.texts[-1], "Upload complete ✅")

    async def test_metadata_remux_keeps_final_upload_filename(self):
        message = FakeMessage()
        client = FakeClient(b"sample-media-data")

        async def fake_run_process(argv, *, timeout, cancel_event=None):
            output_path = argv[-1]
            with open(output_path, "wb") as out:
                out.write(b"remuxed-media-data")
            return 0, "", ""

        with (
            patch.object(AshutoshGoswami24, "get_format_template", new=AsyncMock(return_value="{title} S{season} EP{episode} [{quality}]")),
            patch.object(AshutoshGoswami24, "get_media_preference", new=AsyncMock(return_value="document")),
            patch.object(AshutoshGoswami24, "get_metadata", new=AsyncMock(return_value=True)),
            patch.object(AshutoshGoswami24, "get_title", new=AsyncMock(return_value="Test title")),
            patch.object(AshutoshGoswami24, "get_author", new=AsyncMock(return_value=None)),
            patch.object(AshutoshGoswami24, "get_artist", new=AsyncMock(return_value=None)),
            patch.object(AshutoshGoswami24, "get_audio", new=AsyncMock(return_value=None)),
            patch.object(AshutoshGoswami24, "get_subtitle", new=AsyncMock(return_value=None)),
            patch.object(AshutoshGoswami24, "get_video", new=AsyncMock(return_value=None)),
            patch.object(AshutoshGoswami24, "get_thumbnail", new=AsyncMock(return_value=None)),
            patch.object(AshutoshGoswami24, "get_caption", new=AsyncMock(return_value=None)),
            patch("plugins.file_rename.run_process", new=fake_run_process),
        ):
            await auto_rename_files(client, message)

        self.assertEqual(len(client.sent), 1)
        self.assertEqual(client.sent[0]["filename"], "Series S01 EP02 [1080p].mkv")
        self.assertEqual(client.sent[0]["local_basename"], "Series S01 EP02 [1080p].mkv")
        self.assertNotIn("metadata_", client.sent[0]["filename"])
        self.assertTrue(client.sent[0]["exists_during_upload"])
        self.assertTrue(all(not os.path.exists(path) for path in client.temporary_dirs))

    async def test_initial_status_error_does_not_leave_user_busy_or_temp_files(self):
        message = FakeMessage()
        message.reply_text = AsyncMock(side_effect=RuntimeError("status send failed"))
        client = FakeClient(b"sample-media-data")
        ACTIVE_JOBS.clear()
        original_mkdtemp = tempfile.mkdtemp
        created_dirs = []

        def record_mkdtemp(*args, **kwargs):
            path = original_mkdtemp(*args, **kwargs)
            created_dirs.append(path)
            return path

        with (
            patch.object(AshutoshGoswami24, "get_format_template", new=AsyncMock(return_value="{title}")),
            patch.object(AshutoshGoswami24, "get_media_preference", new=AsyncMock(return_value="document")),
            patch("plugins.file_rename.tempfile.mkdtemp", side_effect=record_mkdtemp),
        ):
            await auto_rename_files(client, message)

        self.assertNotIn(321, ACTIVE_JOBS)
        self.assertEqual(len(client.temporary_dirs), 0)
        self.assertEqual(len(created_dirs), 1)
        self.assertFalse(os.path.exists(created_dirs[0]))


if __name__ == "__main__":
    unittest.main()
