import os
import unittest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

os.environ.setdefault("DB_URL", "mongodb://127.0.0.1:27017")
os.environ.setdefault("API_ID", "12345")
os.environ.setdefault("API_HASH", "test-hash")
os.environ.setdefault("BOT_TOKEN", "123456:TEST")

from pyrogram import Client as PyrogramClient

from bot import Bot
from config import Config


class HealthEndpointToggleTests(unittest.IsolatedAsyncioTestCase):
    async def _start_with_webhook(self, enabled):
        runner = SimpleNamespace(setup=AsyncMock(), cleanup=AsyncMock())
        site = SimpleNamespace(start=AsyncMock())
        user = SimpleNamespace(first_name="Test Bot", mention="@testbot", username="testbot")
        with (
            patch("bot.preflight_plugins"),
            patch.object(PyrogramClient, "start", new=AsyncMock()),
            patch.object(Bot, "get_me", new=AsyncMock(return_value=user)),
            patch.object(Bot, "send_message", new=AsyncMock()),
            patch.object(Config, "WEBHOOK", enabled),
            patch("bot.web.AppRunner", return_value=runner) as app_runner,
            patch("bot.web.TCPSite", return_value=site) as tcp_site,
        ):
            bot = Bot()
            bot.dispatcher.groups = {0: [object()]}
            await bot.start()
        return bot, runner, app_runner, tcp_site

    async def test_disabled_webhook_skips_health_server(self):
        bot, _, app_runner, tcp_site = await self._start_with_webhook(False)
        app_runner.assert_not_called()
        tcp_site.assert_not_called()
        self.assertIsNone(bot._web_runner)

    async def test_enabled_webhook_starts_health_server(self):
        bot, runner, app_runner, tcp_site = await self._start_with_webhook(True)
        app_runner.assert_called_once()
        tcp_site.assert_called_once()
        runner.setup.assert_awaited_once()
        self.assertIs(bot._web_runner, runner)


if __name__ == "__main__":
    unittest.main()
