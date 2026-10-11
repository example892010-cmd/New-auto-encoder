import os
import unittest

os.environ.setdefault("DB_URL", "mongodb://127.0.0.1:27017")

from helper.database import Database


class FakeCollection:
    def __init__(self):
        self.call = None

    async def update_one(self, selector, update, upsert=False):
        self.call = (selector, update, upsert)


class DatabaseUpsertTests(unittest.IsolatedAsyncioTestCase):
    async def test_setting_first_preference_creates_defaults_without_conflicts(self):
        db = object.__new__(Database)
        db.col = FakeCollection()
        await db._update_user(42, {"format_template": "{title} S{season}E{episode}"})
        selector, update, upsert = db.col.call
        self.assertEqual(selector, {"_id": 42})
        self.assertTrue(upsert)
        self.assertEqual(update["$set"]["format_template"], "{title} S{season}E{episode}")
        self.assertNotIn("format_template", update["$setOnInsert"])
        self.assertTrue(update["$setOnInsert"]["metadata"])
        self.assertIsNone(update["$setOnInsert"]["file_id"])

    async def test_existing_user_data_is_not_deleted_by_preference_update(self):
        db = object.__new__(Database)
        db.col = FakeCollection()
        await db._update_user(88, {"media_type": "video"})
        _, update, _ = db.col.call
        self.assertEqual(update["$set"], {"media_type": "video"})
        self.assertNotIn("caption", update["$set"])
        self.assertNotIn("metadata_code", update["$set"])


if __name__ == "__main__":
    unittest.main()
