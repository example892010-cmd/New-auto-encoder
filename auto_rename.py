from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from helper.database import AshutoshGoswami24

@Client.on_message(filters.private & filters.command("autorename"))
async def auto_rename_command(client, message):
    user_id = message.from_user.id

    # Extract the format from the command
    format_template = message.text.split("/autorename", 1)[1].strip()
    if not format_template:
        return await message.reply_text(
            "**Usage:** `/autorename {title} S{season} Ep{episode} [{quality}] [TAMIL]`"
        )

    # Save the format template to the database
    await AshutoshGoswami24.set_format_template(user_id, format_template)

    await message.reply_text("**Auto Rename Format Updated Successfully! ✅**")

@Client.on_message(filters.private & filters.command("setmedia"))
async def set_media_command(client, message):
    user_id = message.from_user.id    
    media_type = message.text.split("/setmedia", 1)[1].strip().lower()
    if media_type not in {"document", "video", "audio"}:
        return await message.reply_text("**Use:** `/setmedia document`, `/setmedia video`, or `/setmedia audio`")

    # Save the preferred media type to the database
    await AshutoshGoswami24.set_media_preference(user_id, media_type)

    await message.reply_text(f"**Media Preference Set To :** {media_type} ✅")






