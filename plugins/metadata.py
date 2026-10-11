from pyrogram import Client, filters
from pyrogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from helper.database import AshutoshGoswami24 as db
from config import Txt


def _value(value):
    return value if value else "Nᴏᴛ ꜰᴏᴜɴᴅ"


async def metadata_text(user_id):
    current = await db.get_metadata(user_id)
    title = await db.get_title(user_id)
    author = await db.get_author(user_id)
    artist = await db.get_artist(user_id)
    audio = await db.get_audio(user_id)
    subtitle = await db.get_subtitle(user_id)
    video = await db.get_video(user_id)

    # Keep compatibility with old users who only have metadata_code saved.
    if not any([title, author, artist, audio, subtitle, video]):
        legacy = await db.get_metadata_code(user_id)
        if legacy:
            title = legacy

    text = (
        f"**㊋ Yᴏᴜʀ Mᴇᴛᴀᴅᴀᴛᴀ ɪꜱ ᴄᴜʀʀᴇɴᴛʟʏ: {'On' if current else 'Off'}**\n\n"
        f"**◈ Tɪᴛʟᴇ ▹** `{_value(title)}`\n"
        f"**◈ Aᴜᴛʜᴏʀ ▹** `{_value(author)}`\n"
        f"**◈ Aʀᴛɪꜱᴛ ▹** `{_value(artist)}`\n"
        f"**◈ Aᴜᴅɪᴏ ▹** `{_value(audio)}`\n"
        f"**◈ Sᴜʙᴛɪᴛʟᴇ ▹** `{_value(subtitle)}`\n"
        f"**◈ Vɪᴅᴇᴏ ▹** `{_value(video)}`"
    )
    buttons = [
        [
            InlineKeyboardButton(f"On{' ✅' if current else ''}", callback_data="on_metadata"),
            InlineKeyboardButton(f"Off{' ✅' if not current else ''}", callback_data="off_metadata"),
        ],
        [InlineKeyboardButton("How to Set Metadata", callback_data="metainfo")],
    ]
    return text, InlineKeyboardMarkup(buttons)


@Client.on_message(filters.private & filters.command("metadata"))
async def metadata(client: Client, message: Message):
    text, keyboard = await metadata_text(message.from_user.id)
    await message.reply_text(text=text, reply_markup=keyboard, disable_web_page_preview=True)


@Client.on_callback_query(filters.regex(r"^(on_metadata|off_metadata|metainfo)$"))
async def metadata_callback(client: Client, query: CallbackQuery):
    user_id = query.from_user.id
    data = query.data

    if data == "metainfo":
        await query.answer()
        await query.message.edit_text(
            text=Txt.META_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup([
                [
                    InlineKeyboardButton("Hᴏᴍᴇ", callback_data="home"),
                    InlineKeyboardButton("Close", callback_data="close"),
                ]
            ]),
        )
        return

    await db.set_metadata(user_id, bool_meta=(data == "on_metadata"))
    await query.answer("Metadata enabled" if data == "on_metadata" else "Metadata disabled")
    text, keyboard = await metadata_text(user_id)
    await query.message.edit_text(text=text, reply_markup=keyboard, disable_web_page_preview=True)


async def _save_field(client, message, setter, label, example):
    if len(message.command) == 1:
        return await message.reply_text(f"**Gɪᴠᴇ Tʜᴇ {label}\n\nExᴀᴍᴩʟᴇ:- {example}**")
    value = message.text.split(" ", 1)[1].strip()
    await setter(message.from_user.id, value)
    await message.reply_text(f"**✅ {label.title()} Sᴀᴠᴇᴅ**")


@Client.on_message(filters.private & filters.command("settitle"))
async def set_title(client, message):
    await _save_field(client, message, db.set_title, "Tɪᴛʟᴇ", "/settitle Encoded By @ANIFLIXANIMETAMIL")


@Client.on_message(filters.private & filters.command("setauthor"))
async def set_author(client, message):
    await _save_field(client, message, db.set_author, "Aᴜᴛʜᴏʀ", "/setauthor @TANJIROKAMADO404")


@Client.on_message(filters.private & filters.command("setartist"))
async def set_artist(client, message):
    await _save_field(client, message, db.set_artist, "Aʀᴛɪꜱᴛ", "/setartist @ANIFLIXANIMETAMIL")


@Client.on_message(filters.private & filters.command("setaudio"))
async def set_audio(client, message):
    await _save_field(client, message, db.set_audio, "Aᴜᴅɪᴏ Tɪᴛʟᴇ", "/setaudio Tamil Audio")


@Client.on_message(filters.private & filters.command("setsubtitle"))
async def set_subtitle(client, message):
    await _save_field(client, message, db.set_subtitle, "Sᴜʙᴛɪᴛʟᴇ Tɪᴛʟᴇ", "/setsubtitle English")


@Client.on_message(filters.private & filters.command("setvideo"))
async def set_video(client, message):
    await _save_field(client, message, db.set_video, "Vɪᴅᴇᴏ Tɪᴛʟᴇ", "/setvideo Encoded By @TANJIROKAMADO404")
