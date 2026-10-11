import asyncio
import importlib
import logging
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

from aiohttp import web
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from pytz import timezone

from config import Config
from route import web_server

PROJECT_ROOT = Path(__file__).resolve().parent
PLUGIN_ROOT = PROJECT_ROOT / "plugins"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("ANIFLIX_RENAME_BOT")
logging.getLogger("pyrogram").setLevel(logging.INFO)


def preflight_plugins() -> dict[int, int]:
    """Import every real plugin and count its declared handlers before startup."""
    os.chdir(PROJECT_ROOT)
    if str(PROJECT_ROOT) not in sys.path:
        sys.path.insert(0, str(PROJECT_ROOT))
    if not PLUGIN_ROOT.is_dir():
        raise RuntimeError(f"Pyrogram plugin directory is missing: {PLUGIN_ROOT}")

    counts: Counter[int] = Counter()
    module_names = []
    for path in sorted(PLUGIN_ROOT.rglob("*.py")):
        if path.name == "__init__.py" or path.name.startswith("_"):
            continue
        relative = path.relative_to(PROJECT_ROOT).with_suffix("")
        module_names.append(".".join(relative.parts))

    if not module_names:
        raise RuntimeError(f"No Python plugin files found in {PLUGIN_ROOT}")

    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
        except Exception:
            logger.exception("Plugin import failed: %s", module_name)
            raise
        module_count = 0
        for value in vars(module).values():
            for handler, group in getattr(value, "handlers", ()):
                if isinstance(group, int):
                    counts[group] += 1
                    module_count += 1
        logger.info("Plugin preflight OK: %s (%d handlers)", module_name, module_count)

    if not sum(counts.values()):
        raise RuntimeError("Plugin preflight completed but found zero Pyrogram handlers")
    logger.info("Plugin preflight handler counts by group: %s", dict(sorted(counts.items())))
    return dict(counts)


class Bot(Client):
    def __init__(self):
        # Smart Plugins discovers from a relative root. Pin the process CWD to the
        # repository root so Render's launch directory cannot silently hide plugins.
        os.chdir(PROJECT_ROOT)
        super().__init__(
            name="ANIFLIX_RENAME_BOT",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            workers=200,
            plugins={"root": "plugins"},
            sleep_threshold=15,
        )
        self._web_runner = None

    async def start(self):
        preflight_plugins()
        await super().start()
        me = await self.get_me()
        self.mention = me.mention
        self.username = me.username

        groups = getattr(self.dispatcher, "groups", {}) or {}
        actual_counts = {int(group): len(handlers) for group, handlers in groups.items() if handlers}
        actual_total = sum(actual_counts.values())
        logger.info("Pyrogram registered handler counts by group: %s", dict(sorted(actual_counts.items())))
        if actual_total == 0:
            logger.error("Pyrogram started without handlers; refusing a misleading healthy startup")
            raise RuntimeError("Pyrogram registered zero handlers after initialization")

        try:
            self._web_runner = web.AppRunner(await web_server())
            await self._web_runner.setup()
            await web.TCPSite(self._web_runner, "0.0.0.0", Config.PORT).start()
        except Exception:
            logger.exception("Optional Render health web service could not be started")

        logger.info("%s started successfully | Pyrogram %s | Layer %s", me.first_name, __version__, layer)

        for admin in Config.ADMIN:
            try:
                await self.send_message(admin, f"**{me.first_name} started successfully.**")
            except Exception:
                logger.exception("Could not notify admin %s", admin)

        if Config.LOG_CHANNEL:
            try:
                now = datetime.now(timezone("Asia/Kolkata"))
                await self.send_message(
                    Config.LOG_CHANNEL,
                    f"**{me.mention} restarted successfully!**\n\n"
                    f"📅 Date: `{now.strftime('%d %B, %Y')}`\n"
                    f"⏰ Time: `{now.strftime('%I:%M:%S %p')}`\n"
                    "🌐 Timezone: `Asia/Kolkata`\n"
                    f"🤖 Version: `v{__version__} (Layer {layer})`",
                )
            except Exception:
                logger.exception("Optional startup log channel notification failed")

    async def stop(self, *args):
        if self._web_runner is not None:
            await self._web_runner.cleanup()
            self._web_runner = None
        await super().stop()
        logger.info("Bot stopped.")


async def main():
    if not Config.API_ID or not Config.API_HASH or not Config.BOT_TOKEN or not Config.DB_URL:
        raise RuntimeError("Set API_ID, API_HASH, BOT_TOKEN, and DB_URL in the Render environment")
    bot = Bot()
    await bot.start()
    try:
        await asyncio.Event().wait()
    finally:
        await bot.stop()


if __name__ == "__main__":
    asyncio.run(main())
