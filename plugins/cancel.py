from pyrogram import Client, filters

from helper.job_control import ACTIVE_JOBS


@Client.on_message(filters.private & filters.command("cancel"))
async def cancel_media_job(_, message):
    user_id = message.from_user.id
    event = ACTIVE_JOBS.get(user_id)
    if not event:
        return await message.reply_text("There is no active media job to cancel.")
    event.set()
    await message.reply_text("Cancellation requested. The current download/FFmpeg step will stop safely.")
