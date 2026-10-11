import os
from pyrogram import Client, filters
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ForceReply,
    CallbackQuery,
    Message,
    InputMediaPhoto,
)

from helper.database import AshutoshGoswami24
from config import Config, Txt


@Client.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user = message.from_user
    await AshutoshGoswami24.add_user(client, message)
    button = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📢 Updates", url="https://t.me/+1CcAFHLS2tU4YWVl"),
                InlineKeyboardButton("💬 Support", url="https://t.me/+1jDuhUQ41hA1YmVl"),
            ],
            [
                InlineKeyboardButton("⚙️ Help", callback_data="help"),
                InlineKeyboardButton("💙 About", callback_data="about"),
            ],
            [
                InlineKeyboardButton(
                    "🧑‍💻 Developer 🧑‍💻", url="https://t.me/TANJIROKAMADO404"
                )
            ],
            [
                InlineKeyboardButton(
                    "⚠️ Issues? Contact Dev", url="https://t.me/TANJIROKAMADO404"
                )
            ],
        ]
    )
    start_pic = Config.START_PIC
    local_start_pic = os.path.join(os.path.dirname(os.path.dirname(__file__)), "helper", "start_pic.jpg")
    if start_pic and not start_pic.startswith(("https://t.me/", "http://t.me/", "https://telegram.me/", "http://telegram.me/")):
        await message.reply_photo(
            start_pic,
            caption=Txt.START_TXT.format(user.first_name),
            reply_markup=button,
        )
    elif os.path.exists(local_start_pic):
        await message.reply_photo(
            local_start_pic,
            caption=Txt.START_TXT.format(user.first_name),
            reply_markup=button,
        )
    else:
        await message.reply_text(
            text=Txt.START_TXT.format(user.first_name),
            reply_markup=button,
            disable_web_page_preview=True,
        )


@Client.on_callback_query()
async def cb_handler(client, query: CallbackQuery):
    await query.answer()
    data = query.data
    user_id = query.from_user.id

    if data == "home":
        await query.message.edit_text(
            text=Txt.START_TXT.format(query.from_user.first_name),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("📢 Updates", url="https://t.me/+1CcAFHLS2tU4YWVl"),
                        InlineKeyboardButton(
                            "💬 Support", url="https://t.me/+1jDuhUQ41hA1YmVl"
                        ),
                    ],
                    [
                        InlineKeyboardButton("⚙️ Help", callback_data="help"),
                        InlineKeyboardButton("💙 About", callback_data="about"),
                    ],
                    [
                        InlineKeyboardButton(
                            "🧑‍💻 Developer 🧑‍💻", url="https://t.me/TANJIROKAMADO404"
                        )
                    ],
                ]
            ),
        )
    elif data == "caption":
        await query.message.edit_text(
            text=Txt.CAPTION_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✖️ Close", callback_data="close"),
                        InlineKeyboardButton("🔙 Back", callback_data="help"),
                    ]
                ]
            ),
        )
    elif data == "help":
        await query.message.edit_text(
            text=Txt.HELP_TXT.format(client.mention),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            "⚙️ Setup AutoRename Format ⚙️", callback_data="file_names"
                        )
                    ],
                    [
                        InlineKeyboardButton("🖼️ Thumbnail", callback_data="thumbnail"),
                        InlineKeyboardButton("✏️ Caption", callback_data="caption"),
                    ],
                    [
                        InlineKeyboardButton("🏠 Home", callback_data="home"),
                        InlineKeyboardButton("💰 Donate", callback_data="donate"),
                    ],
                ]
            ),
        )
    elif data == "donate":
        await query.message.edit_text(
            text=Txt.DONATE_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✖️ Close", callback_data="close"),
                        InlineKeyboardButton("🔙 Back", callback_data="help"),
                    ]
                ]
            ),
        )

    elif data == "file_names":
        format_template = await AshutoshGoswami24.get_format_template(user_id)
        await query.message.edit_text(
            text=Txt.FILE_NAME_TXT.format(format_template=format_template),
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✖️ Close", callback_data="close"),
                        InlineKeyboardButton("🔙 Back", callback_data="help"),
                    ]
                ]
            ),
        )

    elif data == "thumbnail":
        await query.message.edit_text(
            text=Txt.THUMBNAIL_TXT,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✖️ Close", callback_data="close"),
                        InlineKeyboardButton("🔙 Back", callback_data="help"),
                    ]
                ]
            ),
        )

    elif data == "about":
        await query.message.edit_text(
            text=Txt.ABOUT_TXT,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("✖️ Close", callback_data="close"),
                        InlineKeyboardButton("🔙 Back", callback_data="home"),
                    ]
                ]
            ),
        )

    elif data == "close":
        try:
            await query.message.delete()
        except Exception:
            pass
        return
