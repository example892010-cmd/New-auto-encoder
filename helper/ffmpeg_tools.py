"""Safe FFmpeg command construction and cancellable subprocess execution."""
from __future__ import annotations

import asyncio
from collections.abc import Mapping
from collections.abc import Awaitable, Callable


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
        *metadata_arguments(fields), "-progress", "pipe:1", "-stats_period", "1", "-nostats", output_path,
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
        *(metadata_arguments(fields or {})), "-progress", "pipe:1", "-stats_period", "1", "-nostats", output_path,
    ]


def _parse_progress_time(values: dict[str, str]) -> float | None:
    timestamp = values.get("out_time")
    if timestamp and timestamp != "N/A":
        try:
            hours, minutes, seconds = timestamp.split(":", 2)
            return max(0.0, int(hours) * 3600 + int(minutes) * 60 + float(seconds))
        except (TypeError, ValueError):
            pass
    # FFmpeg's out_time_ms field is in microseconds despite its historical name.
    for key in ("out_time_us", "out_time_ms"):
        try:
            return max(0.0, int(values[key]) / 1_000_000)
        except (KeyError, TypeError, ValueError):
            continue
    return None


async def _read_progress_stdout(
    stream,
    progress_callback: Callable[[float], Awaitable[None]] | None,
) -> str:
    output = []
    fields: dict[str, str] = {}
    while True:
        raw = await stream.readline()
        if not raw:
            break
        line = raw.decode(errors="replace")
        output.append(line)
        key, separator, value = line.rstrip("\r\n").partition("=")
        if not separator:
            continue
        fields[key] = value
        if key == "progress":
            current = _parse_progress_time(fields)
            if progress_callback and current is not None:
                await progress_callback(current)
            fields.clear()
    return "".join(output)


async def probe_duration(
    input_path: str,
    *,
    timeout: int = 30,
    cancel_event: asyncio.Event | None = None,
) -> float | None:
    """Return media duration in seconds, or None if ffprobe cannot read it."""
    if cancel_event and cancel_event.is_set():
        raise MediaProcessingCancelled("Processing cancelled by user")
    proc = await asyncio.create_subprocess_exec(
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", input_path,
        stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
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
            raise TimeoutError(f"ffprobe exceeded {timeout} seconds")
        stdout, _ = communicate.result()
        if proc.returncode != 0:
            return None
        try:
            duration = float(stdout.decode(errors="replace").strip())
            return duration if duration > 0 else None
        except (TypeError, ValueError):
            return None
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


async def run_process(
    argv: list[str],
    *,
    timeout: int,
    cancel_event: asyncio.Event | None = None,
    progress_callback: Callable[[float], Awaitable[None]] | None = None,
) -> tuple[int, str, str]:
    """Run without a shell, stream FFmpeg progress, and respect timeout/cancel."""
    proc = await asyncio.create_subprocess_exec(
        *argv, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout_task = asyncio.create_task(_read_progress_stdout(proc.stdout, progress_callback))
    stderr_task = asyncio.create_task(proc.stderr.read())
    wait_task = asyncio.create_task(proc.wait())
    cancel_wait = asyncio.create_task(cancel_event.wait()) if cancel_event else None
    try:
        wait_set = {wait_task}
        if cancel_wait:
            wait_set.add(cancel_wait)
        done, _ = await asyncio.wait(wait_set, timeout=timeout, return_when=asyncio.FIRST_COMPLETED)
        if wait_task not in done:
            if cancel_event and cancel_event.is_set():
                raise MediaProcessingCancelled("Processing cancelled by user")
            raise TimeoutError(f"Process exceeded {timeout} seconds")
        stdout = await stdout_task
        stderr = (await stderr_task).decode(errors="replace")
        return proc.returncode or 0, stdout, stderr
    except BaseException:
        if proc.returncode is None:
            proc.terminate()
            try:
                await asyncio.wait_for(proc.wait(), timeout=5)
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
        for task in (stdout_task, stderr_task, wait_task):
            if not task.done():
                task.cancel()
        await asyncio.gather(stdout_task, stderr_task, wait_task, return_exceptions=True)
        raise
    finally:
        if cancel_wait and not cancel_wait.done():
            cancel_wait.cancel()
        if cancel_wait:
            try:
                await cancel_wait
            except asyncio.CancelledError:
                pass
