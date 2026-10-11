import asyncio
import os
from pathlib import Path
import unittest
from types import SimpleNamespace

os.environ.setdefault("DB_URL", "mongodb://127.0.0.1:27017")
os.environ.setdefault("DB_NAME", "autorename_test")
os.environ.setdefault("API_ID", "12345")
os.environ.setdefault("API_HASH", "test-hash")
os.environ.setdefault("BOT_TOKEN", "123456:TEST")

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, User

from bot import preflight_plugins


class PluginRegistrationTests(unittest.TestCase):
    def test_preflight_imports_all_plugins_and_reports_nonzero_groups(self):
        counts = preflight_plugins()
        self.assertGreater(sum(counts.values()), 0)
        self.assertEqual(counts.get(-1), 2)  # force-subscription message + callback
        self.assertEqual(counts.get(0), 27)

    def test_preflight_anchors_plugin_path_when_started_outside_repository(self):
        original = os.getcwd()
        try:
            os.chdir("/tmp")
            counts = preflight_plugins()
            self.assertGreater(sum(counts.values()), 0)
            self.assertEqual(Path.cwd(), Path(__file__).resolve().parents[1])
        finally:
            os.chdir(original)

    def test_pyrogram_loader_loads_from_the_repository_plugin_package(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            client = Client(
                "test-plugin-loader",
                api_id=12345,
                api_hash="test-hash",
                bot_token="123456:TEST",
                plugins={"root": "plugins"},
            )
            # Pyrogram 2.0.80's loader imports each module and attaches handlers
            # to the client without a Telegram connection.
            client.load_plugins()
            # The loader schedules dispatcher.add_handler tasks on the event
            # loop; reading groups before yielding can produce the reported {}.
            self.assertEqual(dict(client.dispatcher.groups), {})
            loop.run_until_complete(asyncio.sleep(0.05))
            actual = {group: len(items) for group, items in client.dispatcher.groups.items()}
            self.assertEqual(actual, {-1: 2, 0: 27})
        finally:
            loop.close()
            asyncio.set_event_loop(None)

    def test_required_command_functions_exist_and_are_decorated(self):
        from plugins import admin_panel, auto_rename, metadata, start_and_callbacks

        command_handlers = {
            "start": start_and_callbacks.start,
            "help": start_and_callbacks.help_command,
            "about": start_and_callbacks.about_command,
            "tutorial": admin_panel.tutorial,
            "ping": admin_panel.ping,
            "autorename": auto_rename.auto_rename_command,
            "setmedia": auto_rename.set_media_command,
            "metadata": metadata.metadata,
        }
        for command, callback in command_handlers.items():
            with self.subTest(command=command):
                self.assertTrue(getattr(callback, "handlers", None), f"/{command} has no Pyrogram handler")

    def test_callback_dispatchers_are_scoped_not_global_catchalls(self):
        from plugins import start_and_callbacks

        callback_handlers = getattr(start_and_callbacks.menu_callback, "handlers", [])
        self.assertEqual(len(callback_handlers), 1)
        self.assertIsNotNone(callback_handlers[0][0].filters)

    def test_command_filters_match_required_commands_and_bot_mentions(self):
        client = SimpleNamespace(me=SimpleNamespace(username="aniflix_bot"))
        cases = (
            ("help", "/help"),
            ("about", "/about"),
            ("autorename", "/autorename@aniflix_bot {title} S{season} EP{episode}"),
            ("setmedia", "/setmedia video"),
            ("metadata", "/metadata"),
        )
        for command, text in cases:
            with self.subTest(command=command):
                message = SimpleNamespace(text=text, caption=None, command=None)
                self.assertTrue(asyncio.run(filters.command(command)(client, message)))
                self.assertEqual(message.command[0], command)

    def test_unrelated_callbacks_bypass_the_menu_handler(self):
        from plugins import start_and_callbacks

        menu_filter = start_and_callbacks.menu_callback.handlers[0][0].filters
        user = User(id=7, is_bot=False, first_name="Test")
        for data in ("on_metadata", "off_metadata", "metainfo", "check_subscription"):
            query = CallbackQuery(id="query", from_user=user, chat_instance="chat", data=data)
            self.assertFalse(asyncio.run(menu_filter(None, query)), data)
        query = CallbackQuery(id="query", from_user=user, chat_instance="chat", data="help")
        self.assertTrue(asyncio.run(menu_filter(None, query)))


if __name__ == "__main__":
    unittest.main()
