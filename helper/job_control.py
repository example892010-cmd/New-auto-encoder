"""In-memory cancellation signals for active media jobs."""
from __future__ import annotations

import asyncio

ACTIVE_JOBS: dict[int, asyncio.Event] = {}
