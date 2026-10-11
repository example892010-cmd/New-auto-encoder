import logging
import os

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config import Config, Txt
from helper.database import AshutoshGoswami24

logger = logging.getLogger(__name__)


def home_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📢 Updates", url="https://t.me/+1CcAFHLS2tU4YWVl"),
                InlineKeyboardButton("💬 Support", url="https://t.me/+1jDuhUQ41hA1YmVl"),
            ],
            [
                InlineKeyboardButton("⚙️ Help", callback_data="help"),
                InlineKeyboardButton("💙 About", callback_data="about"),
            ],
            [InlineKeyboardButton("🧑‍💻 Developer", url="https://t.me/TANJIROKAMADO404")],
        ]
    )


def help_keyboard():
    return InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("⚙️ Rename format", callback_data="file_names")],
            [InlineKeyboardButton("🖼️ Thumbnail", callback_data="thumbnail"), InlineKeyboardButton("✏️ Caption", callback_data="caption")],
            [InlineKeyboardButton("🏠 Home", callback_data="home")],
        ]
    )


@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    if user is None:
        return
    await AshutoshGoswami24.add_user(client, message)

    if Config.LOG_CHANNEL:
        try:
            username = f"@{user.username}" if user.username else "No username"
            await client.send_message(
                Config.LOG_CHANNEL,
                f"🚀 **{user.first_name} started the bot**\n\n"
                f"👤 Name: {user.first_name}\n🆔 ID: `{user.id}`\n🔗 Username: {username}",
            )
        except Exception:
            logger.exception("Optional new-user log failed for user %s", user.id)

    local_start_pic = os.path.join(os.path.dirname(os.path.dirname(__file__)), "helper", "start_pic.jpg")
    text = Txt.START_TXT.format(user.first_name or "there")
    start_pic = Config.START_PIC
    if start_pic and not start_pic.startswith(("https://t.me/", "http://t.me/", "https://telegram.me/", "http://telegram.me/")):
        await message.reply_photo(start_pic, caption=text, reply_markup=home_keyboard())
    elif os.path.exists(local_start_pic):
        await message.reply_photo(local_start_pic, caption=text, reply_markup=home_keyboard())
    else:
        await message.reply_text(text, reply_markup=home_keyboard(), disable_web_page_preview=True)


@Client.on_message(filters.private & filters.command("help"))
async def help_command(client, message):
    await message.reply_text(
        Txt.HELP_TXT.format(getattr(client, "mention", None) or "ANIFLIX"),
        reply_markup=help_keyboard(),
        disable_web_page_preview=True,
    )


@Client.on_message(filters.private & filters.command("about"))
async def about_command(_, message):
    await message.reply_text(Txt.ABOUT_TXT, disable_web_page_preview=True)


# A broad callback handler would swallow metadata and force-subscription actions.
@Client.on_callback_query(filters.regex(r"^(home|caption|help|donate|file_names|thumbnail|about|close)$"))
async def menu_callback(client, query: CallbackQuery):
    data = query.data or ""
    if data == "close":
        await query.answer()
        try:
            await query.message.delete()
        except Exception:
            logger.debug("Could not delete callback message", exc_info=True)
        return

    await query.answer()
    if data == "home":
        return await query.message.edit_text(
            Txt.START_TXT.format(query.from_user.first_name or "there"),
            disable_web_page_preview=True,
            reply_markup=home_keyboard(),
        )
    if data == "help":
        return await query.message.edit_text(
            Txt.HELP_TXT.format(getattr(client, "mention", None) or "ANIFLIX"),
            disable_web_page_preview=True,
            reply_markup=help_keyboard(),
        )
    if data == "about":
        return await query.message.edit_text(
            Txt.ABOUT_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔙 Back", callback_data="home")]]),
        )
    if data == "caption":
        text = Txt.CAPTION_TXT
    elif data == "thumbnail":
        text = Txt.THUMBNAIL_TXT
    elif data == "donate":
        text = Txt.DONATE_TXT
    else:
        template = await AshutoshGoswami24.get_format_template(query.from_user.id)
        text = Txt.FILE_NAME_TXT.format(format_template=template or "Not set")

    await query.message.edit_text(
        text,
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("✖️ Close", callback_data="close"), InlineKeyboardButton("🔙 Back", callback_data="help")]]
        ),
    )
