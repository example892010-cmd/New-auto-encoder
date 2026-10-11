from pyrogram import Client, filters
from pyrogram.errors import ChannelInvalid, ChatAdminRequired, PeerIdInvalid, UserNotParticipant
from pyrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup

from config import Config

FORCE_SUB_CHANNELS = Config.FORCE_SUB_CHANNELS


async def not_subscribed(_, __, message):
    if not FORCE_SUB_CHANNELS or not message.from_user:
        return False
    for channel in FORCE_SUB_CHANNELS:
        try:
            member = await message._client.get_chat_member(channel, message.from_user.id)
            if str(member.status).lower().endswith(("left", "kicked")):
                return True
        except UserNotParticipant:
            return True
        except (ChatAdminRequired, PeerIdInvalid, ChannelInvalid):
            # Preserve the existing fail-open behavior for inaccessible optional channels.
            continue
    return False


@Client.on_message(filters.private & filters.create(not_subscribed), group=-1)
async def forces_sub(client, message):
    if not message.from_user:
        return
    not_joined = []
    for channel in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(channel, message.from_user.id)
            if str(member.status).lower().endswith(("left", "kicked")):
                not_joined.append(channel)
        except UserNotParticipant:
            not_joined.append(channel)
        except (ChatAdminRequired, PeerIdInvalid, ChannelInvalid):
            continue

    buttons = [
        [InlineKeyboardButton(f"📢 Join {channel.lstrip('@')} 📢", url=f"https://t.me/{channel.lstrip('@')}")]
        for channel in not_joined
    ]
    buttons.append([InlineKeyboardButton("✅ I am joined", callback_data="check_subscription")])
    await message.reply_text(
        "**Sorry, you're not joined to all required channels. Please join the update channels to continue.**",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


@Client.on_callback_query(filters.regex(r"^check_subscription$"), group=-1)
async def check_subscription(client, query: CallbackQuery):
    await query.answer("Checking subscription…")
    not_joined = []
    for channel in FORCE_SUB_CHANNELS:
        try:
            member = await client.get_chat_member(channel, query.from_user.id)
            if str(member.status).lower().endswith(("left", "kicked")):
                not_joined.append(channel)
        except UserNotParticipant:
            not_joined.append(channel)
        except (ChatAdminRequired, PeerIdInvalid, ChannelInvalid):
            continue

    if not not_joined:
        return await query.message.edit_text("**You have joined all required channels. Thank you! 😊 Use /start now.**")
    buttons = [
        [InlineKeyboardButton(f"📢 Join {channel.lstrip('@')} 📢", url=f"https://t.me/{channel.lstrip('@')}")]
        for channel in not_joined
    ]
    buttons.append([InlineKeyboardButton("✅ Check again", callback_data="check_subscription")])
    await query.message.edit_text(
        "**You haven't joined all required channels. Please join them to continue.**",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
