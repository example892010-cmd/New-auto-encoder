"""Safe FFmpeg command construction and cancellable subprocess execution."""
from __future__ import annotations

import asyncio
from collections.abc import Mapping


class MediaProcessingCancelled(Exception):
    """Raised when the user cancels an FFmpeg operation."""


def metadata_arguments(fields: Mapping[str, str | None]) -> list[str]:
    """Build flat argv entries for container and stream metadata fields."""
    args: list[str] = []
    for key in ("title", "author", "artist"):
        value = fields.get(key)
        if value:
            args.extend(["-metadata", f"{key}={value}"])
    for stream, key in (("v", "video"), ("a", "audio"), ("s", "subtitle")):
        value = fields.get(key)
        if value:
            args.extend([f"-metadata:s:{stream}", f"title={value}"])
    return args


def build_metadata_command(input_path: str, output_path: str, fields: Mapping[str, str | None]) -> list[str]:
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", input_path,
        "-map", "0", "-c", "copy", "-map_metadata", "0",
        *metadata_arguments(fields), output_path,
    ]


def build_encode_command(
    input_path: str,
    output_path: str,
    resolution: int,
    fields: Mapping[str, str | None] | None = None,
) -> list[str]:
    if resolution not in {480, 720, 1080}:
        raise ValueError("resolution must be one of 480, 720, or 1080")
    # Escape the expression comma for FFmpeg's filter parser. This caps output
    # height at the requested resolution, keeps aspect ratio, and never upscales.
    scale = rf"scale=-2:min(ih\,{resolution})"
    return [
        "ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", input_path,
        "-map", "0", "-map_metadata", "0", "-vf", scale,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "26",
        "-c:a", "copy", "-c:s", "copy",
        *(metadata_arguments(fields or {})), output_path,
    ]


async def run_process(
    argv: list[str], *, timeout: int, cancel_event: asyncio.Event | None = None
) -> tuple[int, str, str]:
    """Run a process without a shell, respecting timeout and optional cancel."""
    proc = await asyncio.create_subprocess_exec(
        *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    communicate = asyncio.create_task(proc.communicate())
    cancel_wait = asyncio.create_task(cancel_event.wait()) if cancel_event else None
    try:
        wait_set = {communicate}
        if cancel_wait:
            wait_set.add(cancel_wait)
        done, _ = await asyncio.wait(wait_set, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
        if communicate not in done:
            if cancel_event and cancel_event.is_set():
                raise MediaProcessingCancelled("Processing cancelled by user")
            raise TimeoutError(f"Process exceeded {timeout} seconds")
        stdout, stderr = communicate.result()
        return proc.returncode or 0, stdout.decode(errors="replace"), stderr.decode(errors="replace")
    except BaseException:
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
        if not communicate.done():
            communicate.cancel()
        try:
            await communicate
        except BaseException:
            pass
        raise
    finally:
        if cancel_wait and not cancel_wait.done():
            cancel_wait.cancel()
        if cancel_wait:
            try:
                await cancel_wait
            except asyncio.CancelledError:
                pass
