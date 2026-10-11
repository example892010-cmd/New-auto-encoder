"""MongoDB persistence for user preferences and existing user records."""
from __future__ import annotations

import logging

import motor.motor_asyncio

from config import Config
from helper.utils import send_log

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, uri: str, database_name: str):
        if not uri:
            raise ValueError("DB_URL environment variable is required")
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri, serverSelectionTimeoutMS=10000)
        self.database = self._client[database_name]
        # Retain this historical attribute name for compatibility.
        self.AshutoshGoswami24 = self.database
        self.col = self.database.user

    @staticmethod
    def new_user(user_id: int) -> dict:
        return {
            "_id": int(user_id),
            "file_id": None,
            "caption": None,
            "metadata": True,
            "metadata_code": "Telegram : @ANIFLIXANIMETAMIL",
            "metadata_title": None,
            "metadata_author": None,
            "metadata_artist": None,
            "metadata_audio": None,
            "metadata_subtitle": None,
            "metadata_video": None,
            "format_template": None,
            "media_type": None,
        }

    async def _update_user(self, user_id: int, values: dict) -> None:
        defaults = self.new_user(user_id)
        defaults.pop("_id", None)
        for field in values:
            defaults.pop(field, None)
        await self.col.update_one(
            {"_id": int(user_id)},
            {"$set": values, "$setOnInsert": defaults},
            upsert=True,
        )

    async def _get_user(self, user_id: int):
        return await self.col.find_one({"_id": int(user_id)})

    async def add_user(self, bot, message):
        user = message.from_user
        if not user:
            return
        try:
            result = await self.col.update_one(
                {"_id": int(user.id)},
                {"$setOnInsert": {key: value for key, value in self.new_user(user.id).items() if key != "_id"}},
                upsert=True,
            )
            if result.upserted_id is not None:
                try:
                    await send_log(bot, user)
                except Exception:
                    logger.exception("Optional new-user log failed for %s", user.id)
        except Exception:
            logger.exception("Could not add user %s", user.id)

    async def is_user_exist(self, user_id):
        try:
            return await self._get_user(user_id) is not None
        except Exception:
            logger.exception("Could not check user %s", user_id)
            return False

    async def total_users_count(self):
        try:
            return await self.col.count_documents({})
        except Exception:
            logger.exception("Could not count users")
            return 0

    async def get_all_users(self):
        return self.col.find({})

    async def delete_user(self, user_id):
        try:
            await self.col.delete_one({"_id": int(user_id)})
        except Exception:
            logger.exception("Could not delete user %s", user_id)

    async def _get_value(self, user_id, field, default=None):
        try:
            user = await self._get_user(user_id)
            return user.get(field, default) if user else default
        except Exception:
            logger.exception("Could not read %s for user %s", field, user_id)
            return default

    async def _set_value(self, user_id, field, value):
        try:
            await self._update_user(user_id, {field: value})
        except Exception:
            logger.exception("Could not save %s for user %s", field, user_id)

    async def set_thumbnail(self, user_id, file_id):
        await self._set_value(user_id, "file_id", file_id)

    async def get_thumbnail(self, user_id):
        return await self._get_value(user_id, "file_id")

    async def set_caption(self, user_id, caption):
        await self._set_value(user_id, "caption", caption)

    async def get_caption(self, user_id):
        return await self._get_value(user_id, "caption")

    async def set_format_template(self, user_id, format_template):
        await self._set_value(user_id, "format_template", format_template)

    async def get_format_template(self, user_id):
        return await self._get_value(user_id, "format_template")

    async def set_media_preference(self, user_id, media_type):
        await self._set_value(user_id, "media_type", media_type)

    async def get_media_preference(self, user_id):
        return await self._get_value(user_id, "media_type")

    async def set_metadata(self, user_id, bool_meta):
        await self._set_value(user_id, "metadata", bool(bool_meta))

    async def get_metadata(self, user_id):
        return await self._get_value(user_id, "metadata", True)

    async def set_metadata_code(self, user_id, metadata_code):
        await self._set_value(user_id, "metadata_code", metadata_code)

    async def get_metadata_code(self, user_id):
        return await self._get_value(user_id, "metadata_code")

    async def set_title(self, user_id, title):
        await self._set_value(user_id, "metadata_title", title)

    async def get_title(self, user_id):
        return await self._get_value(user_id, "metadata_title")

    async def set_author(self, user_id, author):
        await self._set_value(user_id, "metadata_author", author)

    async def get_author(self, user_id):
        return await self._get_value(user_id, "metadata_author")

    async def set_artist(self, user_id, artist):
        await self._set_value(user_id, "metadata_artist", artist)

    async def get_artist(self, user_id):
        return await self._get_value(user_id, "metadata_artist")

    async def set_audio(self, user_id, audio):
        await self._set_value(user_id, "metadata_audio", audio)

    async def get_audio(self, user_id):
        return await self._get_value(user_id, "metadata_audio")

    async def set_subtitle(self, user_id, subtitle):
        await self._set_value(user_id, "metadata_subtitle", subtitle)

    async def get_subtitle(self, user_id):
        return await self._get_value(user_id, "metadata_subtitle")

    async def set_video(self, user_id, video):
        await self._set_value(user_id, "metadata_video", video)

    async def get_video(self, user_id):
        return await self._get_value(user_id, "metadata_video")


AshutoshGoswami24 = Database(Config.DB_URL, Config.DB_NAME)
