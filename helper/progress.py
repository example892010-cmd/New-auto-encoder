"""Throttled Telegram progress updates for transfers and FFmpeg processing."""
from __future__ import annotations

import logging
import os
import time

logger = logging.getLogger(__name__)


def format_bytes(value: int | float) -> str:
    amount = max(0.0, float(value or 0))
    units = ("B", "KB", "MB", "GB", "TB", "PB")
    for unit in units:
        if amount < 1024 or unit == units[-1]:
            return f"{amount:.2f} {unit}"
        amount /= 1024
    return f"{amount:.2f} PB"


def format_eta(seconds: float | None) -> str:
    if seconds is None or seconds < 0 or seconds == float("inf"):
        return "calculating…"
    remaining = max(0, int(seconds))
    units = []
    days, remaining = divmod(remaining, 86400)
    hours, remaining = divmod(remaining, 3600)
    minutes, secs = divmod(remaining, 60)
    if days:
        units.append(f"{days}d")
    if hours:
        units.append(f"{hours}h")
    if minutes:
        units.append(f"{minutes}m")
    if secs or not units:
        units.append(f"{secs}s")
    return ", ".join(units[:2])


class ProgressReporter:
    """Render a compact progress bar while rate-limiting Telegram message edits."""

    def __init__(self, message, heading: str, *, min_interval: float = 1.2):
        self.message = message
        self.heading = heading
        self.min_interval = min_interval
        self.started = time.monotonic()
        self.last_edit = 0.0
        self.last_sample_time = self.started
        self.last_sample_value = 0.0
        self.speed = 0.0
        self.last_media_seconds = 0.0

    async def _publish(self, text: str, *, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self.last_edit < self.min_interval:
            return
        try:
            edit = getattr(self.message, "edit_text", None) or self.message.edit
            await edit(text)
        except Exception:
            # A status edit should never turn a successful transfer into a failed job.
            logger.debug("Could not update Telegram progress message", exc_info=True)
        finally:
            self.last_edit = now

    def _bar(self, percent: float) -> str:
        filled = max(0, min(20, int(percent // 5)))
        return "⬢" * filled + "⬡" * (20 - filled)

    def _text(self, *, percent: float, size_line: str, speed_line: str, eta: str) -> str:
        percent = max(0.0, min(100.0, percent))
        return (
            f"{self.heading}\n\n"
            f"{self._bar(percent)}\n"
            "╭━━━━❰ᴘʀᴏɢʀᴇss ʙᴀʀ❱━➣\n"
            f"┣⪼ 🗃️ Sɪᴢᴇ: {size_line}\n"
            f"┣⪼ ⏳️ Dᴏɴᴇ : {percent:.1f}%\n"
            f"┣⪼ 🚀 Sᴩᴇᴇᴅ: {speed_line}\n"
            f"┣⪼ ⏰️ ETA: {eta}\n"
            "╰━━━━━━━━━━━━━━━➣"
        )

    def _sample_speed(self, current: float) -> float:
        now = time.monotonic()
        delta_t = max(now - self.last_sample_time, 0.001)
        instant = max(0.0, current - self.last_sample_value) / delta_t
        if instant > 0:
            self.speed = instant if self.speed <= 0 else (self.speed * 0.65 + instant * 0.35)
        self.last_sample_time = now
        self.last_sample_value = current
        return self.speed

    async def begin_transfer(self, total: int) -> None:
        total = max(0, int(total or 0))
        await self.transfer(0, total, force=True)

    async def transfer(self, current: int, total: int, *_args, force: bool = False) -> None:
        current = max(0, int(current or 0))
        total = max(0, int(total or 0))
        speed = self._sample_speed(current)
        percent = (current * 100.0 / total) if total else 0.0
        eta = (total - current) / speed if speed > 0 and total else None
        self.heading = self.heading.split("\n", 1)[0]
        text = self._text(
            percent=percent,
            size_line=f"{format_bytes(current)} | {format_bytes(total)}",
            speed_line=f"{format_bytes(speed)}/s",
            eta=format_eta(eta),
        )
        await self._publish(text, force=force or (total > 0 and current >= total))

    async def media(
        self,
        current_seconds: float,
        total_seconds: float | None,
        output_path: str,
        source_size: int,
        *,
        force: bool = False,
        complete: bool = False,
    ) -> None:
        current_seconds = max(0.0, float(current_seconds or 0))
        self.last_media_seconds = max(self.last_media_seconds, current_seconds)
        elapsed = max(time.monotonic() - self.started, 0.001)
        total = float(total_seconds or 0)
        percent = 100.0 if complete else (current_seconds * 100.0 / total if total > 0 else 0.0)
        realtime = current_seconds / elapsed
        eta = ((total - current_seconds) / realtime) if total > 0 and realtime > 0 else None
        try:
            output_size = os.path.getsize(output_path)
        except OSError:
            output_size = 0
        self.heading = self.heading.split("\n", 1)[0]
        speed = f"{realtime:.2f}× realtime" if current_seconds > 0 else "calculating…"
        text = self._text(
            percent=percent,
            size_line=f"{format_bytes(output_size)} output | {format_bytes(source_size)} input",
            speed_line=speed,
            eta="0s" if complete else format_eta(eta),
        )
        await self._publish(text, force=force or complete)
