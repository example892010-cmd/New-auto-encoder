import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from pyrogram.errors import UserNotParticipant, ChatAdminRequired, PeerIdInvalid, ChannelInvalid
from config import Config

FORCE_SUB_CHANNELS = Config.FORCE_SUB_CHANNELS


async def not_subscribed(_, __, message):
    for channel in FORCE_SUB_CHANNELS:
        try:
            user = await message._client.get_chat_member(channel, message.from_user.id)
            if user.status in {"kicked", "left"}:
                return True
        except (UserNotParticipant, ChatAdminRequired, PeerIdInvalid, ChannelInvalid):
            continue
    return False


@Client.on_message(filters.private & filters.create(not_subscribed))
async def forces_sub(client, message):
    not_joined_channels = []
    for channel in FORCE_SUB_CHANNELS:
        try:
            user = await client.get_chat_member(channel, message.from_user.id)
            if user.status in {"kicked", "left"}:
                not_joined_channels.append(channel)
        except UserNotParticipant:
            not_joined_channels.append(channel)
        except (ChatAdminRequired, PeerIdInvalid, ChannelInvalid):
            continue

    buttons = [
        [
            InlineKeyboardButton(
                text=f"📢 Join {channel.lstrip('@')} 📢", url=f"https://t.me/{channel.lstrip('@')}"
            )
        ]
        for channel in not_joined_channels
    ]
    buttons.append(
        [
            InlineKeyboardButton(
                text="✅ I am joined ✅", callback_data="check_subscription"
            )
        ]
    )

    text = "**Sorry, you're not joined to all required channels 😐. Please join the update channels to continue**"
    await message.reply_text(text=text, reply_markup=InlineKeyboardMarkup(buttons))


@Client.on_callback_query(filters.regex("check_subscription"))
async def check_subscription(client, callback_query: CallbackQuery):
    await callback_query.answer("Checking subscription...", show_alert=False)
    user_id = callback_query.from_user.id
    not_joined_channels = []

    for channel in FORCE_SUB_CHANNELS:
        try:
            user = await client.get_chat_member(channel, user_id)
            if user.status in {"kicked", "left"}:
                not_joined_channels.append(channel)
        except UserNotParticipant:
            not_joined_channels.append(channel)
        except (ChatAdminRequired, PeerIdInvalid, ChannelInvalid):
            continue

    if not not_joined_channels:
        await callback_query.message.edit_text(
            "**You have joined all the required channels. Thank you! 😊 /start now**"
        )
    else:
        buttons = [
            [
                InlineKeyboardButton(
                    text=f"📢 Join {channel.capitalize()} 📢",
                    url=f"https://t.me/{channel}",
                )
            ]
            for channel in not_joined_channels
        ]
        buttons.append(
            [
                InlineKeyboardButton(
                    text="✅ I am joined", callback_data="check_subscription"
                )
            ]
        )

        text = "**You haven't joined all the required channels. Please join them to continue. **"
        await callback_query.message.edit_text(
            text=text, reply_markup=InlineKeyboardMarkup(buttons)
        )
