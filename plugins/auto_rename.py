from pyrogram import Client, filters

from helper.database import AshutoshGoswami24


@Client.on_message(filters.private & filters.command("autorename"))
async def auto_rename_command(client, message):
    args = message.command[1:]
    format_template = " ".join(args).strip()
    if not format_template:
        return await message.reply_text(
            "**Usage:** `/autorename {title} S{season} Ep{episode} [{quality}] [TAMIL]`"
        )

    await AshutoshGoswami24.set_format_template(message.from_user.id, format_template)
    await message.reply_text("**Auto Rename Format Updated Successfully! ✅**")


@Client.on_message(filters.private & filters.command("setmedia"))
async def set_media_command(client, message):
    args = message.command[1:]
    media_type = " ".join(args).strip().lower()
    if media_type not in {"document", "video", "audio"}:
        return await message.reply_text(
            "**Use:** `/setmedia document`, `/setmedia video`, or `/setmedia audio`"
        )

    await AshutoshGoswami24.set_media_preference(message.from_user.id, media_type)
    await message.reply_text(f"**Media Preference Set To: {media_type} ✅**")
