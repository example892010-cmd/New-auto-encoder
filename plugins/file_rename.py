from __future__ import annotations

import asyncio
import logging
import os
import shutil
import tempfile
from pathlib import Path

from PIL import Image
from pyrogram import Client, filters
from pyrogram.errors import FloodWait

from config import Config
from helper.database import AshutoshGoswami24
from helper.ffmpeg_tools import (
    MediaProcessingCancelled,
    build_encode_command,
    build_metadata_command,
    run_process,
)
from helper.filename import render_template
from helper.job_control import ACTIVE_JOBS
from helper.utils import convert, humanbytes

logger = logging.getLogger(__name__)
VIDEO_EXTENSIONS = {".mp4", ".mkv", ".mov", ".avi", ".webm", ".m4v", ".mpeg", ".mpg", ".ts"}


def _caption(template, filename, size, duration):
    if not template:
        return f"**{filename}**"
    values = {"filename": filename, "filesize": humanbytes(size), "duration": convert(duration or 0)}
    try:
        return template.format_map(values)
    except (KeyError, ValueError, IndexError):
        logger.warning("Invalid user caption template; using safe default")
        return f"**{filename}**"


async def _get_metadata_fields(user_id):
    enabled = await AshutoshGoswami24.get_metadata(user_id)
    if not enabled:
        return {}
    fields = {
        "title": await AshutoshGoswami24.get_title(user_id),
        "author": await AshutoshGoswami24.get_author(user_id),
        "artist": await AshutoshGoswami24.get_artist(user_id),
        "audio": await AshutoshGoswami24.get_audio(user_id),
        "subtitle": await AshutoshGoswami24.get_subtitle(user_id),
        "video": await AshutoshGoswami24.get_video(user_id),
    }
    if not any(fields.values()):
        legacy = await AshutoshGoswami24.get_metadata_code(user_id)
        if legacy:
            fields["title"] = legacy
    return fields


async def _send_with_floodwait(send_call, *args, **kwargs):
    for attempt in range(4):
        try:
            return await send_call(*args, **kwargs)
        except FloodWait as exc:
            if attempt == 3:
                raise
            await asyncio.sleep(max(1, int(getattr(exc, "value", 1))))


async def _prepare_thumbnail(client, user_id, message, work_dir):
    try:
        thumb_id = await AshutoshGoswami24.get_thumbnail(user_id)
        if not thumb_id and message.video and message.video.thumbs:
            thumb_id = message.video.thumbs[0].file_id
        if not thumb_id:
            return None
        source = await client.download_media(thumb_id, file_name=os.path.join(work_dir, "thumb_source"))
        if not source:
            return None
        destination = os.path.join(work_dir, "thumb.jpg")
        with Image.open(source) as image:
            image = image.convert("RGB")
            image.thumbnail((320, 320))
            image.save(destination, "JPEG", quality=90)
        return destination
    except Exception:
        logger.warning("Saved thumbnail is not a readable image; uploading without it")
        return None


@Client.on_message(filters.private & (filters.document | filters.video | filters.audio))
async def auto_rename_files(client, message):
    if not message.from_user:
        return
    user_id = message.from_user.id
    if user_id in ACTIVE_JOBS:
        return await message.reply_text("A media job is already running. Use /cancel before sending another file.")

    template = await AshutoshGoswami24.get_format_template(user_id)
    if not template:
        return await message.reply_text("Please set an auto-rename format first using /autorename.")

    if message.document:
        media = message.document
        original_name = media.file_name or "document.bin"
        media_kind = "document"
        duration = 0
        file_size = media.file_size or 0
        mime_type = media.mime_type or ""
    elif message.video:
        media = message.video
        original_name = media.file_name or "video.mp4"
        media_kind = "video"
        duration = media.duration or 0
        file_size = media.file_size or 0
        mime_type = "video/unknown"
    else:
        media = message.audio
        original_name = media.file_name or "audio.mp3"
        media_kind = "audio"
        duration = media.duration or 0
        file_size = media.file_size or 0
        mime_type = "audio/unknown"

    extension = Path(original_name).suffix or (".mp4" if media_kind == "video" else ".mp3" if media_kind == "audio" else ".bin")
    extension = extension[:12]
    output_stem = render_template(template, original_name)
    output_name = output_stem + extension
    preferred_kind = await AshutoshGoswami24.get_media_preference(user_id) or media_kind
    if preferred_kind not in {"document", "video", "audio"}:
        preferred_kind = media_kind

    cancel_event = asyncio.Event()
    ACTIVE_JOBS[user_id] = cancel_event
    work_dir = None
    status = None
    try:
        work_dir = tempfile.mkdtemp(prefix=f"aniflix-{user_id}-")
        status = await message.reply_text("Downloading the file…")
        source_path = await client.download_media(
            message,
            file_name=os.path.join(work_dir, "source" + extension),
        )
        if not source_path or not os.path.isfile(source_path):
            raise RuntimeError("Telegram download returned no local file")
        if cancel_event.is_set():
            raise MediaProcessingCancelled("Cancelled after download")

        await status.edit("Preparing renamed file and metadata…")
        renamed_path = os.path.join(work_dir, output_name)
        if os.path.abspath(source_path) != os.path.abspath(renamed_path):
            os.replace(source_path, renamed_path)

        metadata = await _get_metadata_fields(user_id)
        is_video = media_kind == "video" or mime_type.startswith("video/") or extension.lower() in VIDEO_EXTENSIONS
        outputs = []

        if Config.ENCODE_RESOLUTIONS and is_video:
            await status.edit("Encoding configured resolutions…")
            for resolution in Config.ENCODE_RESOLUTIONS:
                if cancel_event.is_set():
                    raise MediaProcessingCancelled("Cancelled before encoding")
                encoded_name = f"{output_stem}_{resolution}p.mkv"
                encoded_path = os.path.join(work_dir, encoded_name)
                command = build_encode_command(renamed_path, encoded_path, resolution, metadata)
                code, _, stderr = await run_process(
                    command, timeout=Config.FFMPEG_TIMEOUT, cancel_event=cancel_event
                )
                if code != 0 or not os.path.isfile(encoded_path):
                    raise RuntimeError(f"FFmpeg failed for {resolution}p: {stderr[-1500:]}")
                outputs.append((encoded_path, encoded_name))
        elif metadata:
            # Use a separate directory so FFmpeg can keep the final basename
            # while still writing to a path distinct from its input.
            metadata_dir = os.path.join(work_dir, "metadata")
            os.makedirs(metadata_dir, exist_ok=True)
            metadata_path = os.path.join(metadata_dir, output_name)
            command = build_metadata_command(renamed_path, metadata_path, metadata)
            code, _, stderr = await run_process(
                command, timeout=Config.FFMPEG_TIMEOUT, cancel_event=cancel_event
            )
            if code == 0 and os.path.isfile(metadata_path):
                outputs.append((metadata_path, output_name))
            else:
                logger.warning("Metadata remux failed; uploading the renamed original: %s", stderr[-1500:])
                outputs.append((renamed_path, output_name))
        else:
            outputs.append((renamed_path, output_name))

        thumb_path = await _prepare_thumbnail(client, user_id, message, work_dir)
        custom_caption = await AshutoshGoswami24.get_caption(user_id)
        await status.edit("Uploading completed file(s)…")
        for index, (path, filename) in enumerate(outputs, start=1):
            if cancel_event.is_set():
                raise MediaProcessingCancelled("Cancelled before upload")
            caption = _caption(custom_caption, filename, file_size, duration)
            if len(outputs) > 1:
                caption = f"{caption}\n\n({index}/{len(outputs)})"
            if preferred_kind == "video":
                await _send_with_floodwait(
                    client.send_video, message.chat.id, video=path, caption=caption,
                    thumb=thumb_path, duration=duration, file_name=filename,
                )
            elif preferred_kind == "audio":
                await _send_with_floodwait(
                    client.send_audio, message.chat.id, audio=path, caption=caption,
                    thumb=thumb_path, duration=duration, file_name=filename,
                )
            else:
                await _send_with_floodwait(
                    client.send_document, message.chat.id, document=path, caption=caption,
                    thumb=thumb_path, file_name=filename,
                )
        await status.edit("Upload complete ✅")
    except MediaProcessingCancelled:
        logger.info("Media job cancelled for user %s", user_id)
        try:
            if status:
                await status.edit("Media processing cancelled. Temporary files were removed.")
        except Exception:
            pass
    except Exception as exc:
        logger.exception("Media processing failed for user %s", user_id)
        try:
            if status:
                await status.edit(f"**Media processing failed:** {str(exc)[:900]}")
        except Exception:
            pass
    finally:
        ACTIVE_JOBS.pop(user_id, None)
        if work_dir:
            shutil.rmtree(work_dir, ignore_errors=True)
