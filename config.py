import os
import re
import time


class Config:
    # Pyrogram client configuration. Secrets are provided only by the environment.
    API_ID = int(os.environ.get("API_ID", "0") or "0")
    API_HASH = os.environ.get("API_HASH", "")
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

    # Database configuration (existing environment variable names retained).
    DB_NAME = os.environ.get("DB_NAME", "autorename")
    DB_URL = os.environ.get("DB_URL", "")

    # Existing bot options.
    BOT_UPTIME = time.time()
    START_PIC = os.environ.get("START_PIC", "")
    ADMIN = []
    for admin in re.split(r"[\s,]+", os.environ.get("ADMIN", "").strip()):
        if admin:
            try:
                ADMIN.append(int(admin))
            except ValueError:
                ADMIN.append(admin.lstrip("@"))

    FORCE_SUB_CHANNELS = [
        item.strip().lstrip("@")
        for item in (os.environ.get("FORCE_SUB_CHANNELS") or os.environ.get("FORCE_SUB") or "").split(",")
        if item.strip()
    ]
    LOG_CHANNEL = int(os.environ.get("LOG_CHANNEL", "0") or "0")
    PORT = int(os.environ.get("PORT", "8080") or "8080")
    WEBHOOK = os.environ.get("WEBHOOK", "True").strip().lower() in {"1", "true", "yes", "on"}

    # Optional global encoding. Empty/unset preserves the current rename/remux-only
    # workflow. Set to e.g. "480,720,1080" to create each requested rendition.
    _resolution_values = os.environ.get("ENCODE_RESOLUTIONS", "").strip()
    ENCODE_RESOLUTIONS = tuple(
        sorted({int(re.sub(r"(?i)p$", "", part.strip())) for part in _resolution_values.split(",") if part.strip()})
    )
    if any(resolution not in {480, 720, 1080} for resolution in ENCODE_RESOLUTIONS):
        raise ValueError("ENCODE_RESOLUTIONS accepts only 480, 720, and/or 1080")
    FFMPEG_TIMEOUT = int(os.environ.get("FFMPEG_TIMEOUT", "1800") or "1800")


class Txt:
    START_TXT = """👋 Hello {}!

➻ Advanced Auto Rename Bot
➻ Custom Thumbnail & Caption
➻ Use /tutorial To Get Started

⚡ Powered By @ANIFLIXANIMETAMIL
👨‍💻 Developer: @TANJIROKAMADO404
"""

    FILE_NAME_TXT = """<b><u>SETUP AUTO RENAME FORMAT</u></b>

Use these keywords to set a custom file name:
✓ <code>{{title}}</code> — Anime / Movie title
✓ <code>{{season}}</code> — Season number
✓ <code>{{episode}}</code> — Episode number
✓ <code>{{quality}}</code> — Source quality

<b>Example:</b>
<code>/autorename {{title}} S{{season}} Ep{{episode}} [{{quality}}] [TAMIL]</code>

<b>Your current format:</b>
<code>{format_template}</code>"""

    ABOUT_TXT = """<b>🤖 My Name:</b> ANIFLIX RENAME BOT ⚡
<b>📝 Language:</b> Python 3
<b>📚 Library:</b> Pyrogram 2.0.80
<b>🚀 Hosting:</b> Render
<b>📢 Channel:</b> @ANIFLIXANIMETAMIL
<b>🧑‍💻 Developer:</b> @TANJIROKAMADO404

<b>♻️ Bot made by:</b> @TANJIROKAMADO404"""

    META_TXT = """<b>🎬 HOW TO SET METADATA</b>

Use these commands to set your metadata:
➻ /settitle — Set container title
➻ /setauthor — Set author
➻ /setartist — Set artist
➻ /setaudio — Set audio stream title
➻ /setsubtitle — Set subtitle stream title
➻ /setvideo — Set video stream title

Example: <code>/settitle Naruto Shippuden</code>
After setting metadata, use /metadata to turn metadata on or off."""
    SEND_METADATA = "<b>Send the metadata text you want to use.</b>"
    THUMBNAIL_TXT = """<b><u>🖼️ HOW TO SET THUMBNAIL</u></b>

Send a photo to save it as your thumbnail.
/viewthumb — View your thumbnail
/delthumb — Delete your thumbnail"""
    CAPTION_TXT = """<b><u>📝 HOW TO SET CAPTION</u></b>

/set_caption — Set a custom caption
/see_caption — View your caption
/del_caption — Delete your caption"""
    PROGRESS_BAR = """<b>
╭━━━━❰ᴘʀᴏɢʀᴇss ʙᴀʀ❱━➣
┣⪼ 🗃️ Sɪᴢᴇ: {1} | {2}
┣⪼ ⏳️ Dᴏɴᴇ : {0}%
┣⪼ 🚀 Sᴩᴇᴇᴅ: {3}/s
┣⪼ ⏰️ ETA: {4}
╰━━━━━━━━━━━━━━━➣ </b>"""
    DONATE_TXT = """<b>Need help?</b>

For issues, contact the developer.
<b>Developer:</b> @TANJIROKAMADO404
<b>Updates:</b> https://t.me/+1CcAFHLS2tU4YWVl
<b>Support:</b> https://t.me/+1jDuhUQ41hA1YmVl"""
    HELP_TXT = """<b>Hey</b> {} 👋

Configure your Auto Rename Bot:
/autorename — Set the filename template
/setmedia — Choose document, video, or audio upload
/metadata — Manage media metadata
/tutorial — Show setup instructions
/ping — Check bot responsiveness

<b>Metadata fields:</b> /settitle, /setauthor, /setartist, /setaudio, /setsubtitle, /setvideo
<b>Caption:</b> /set_caption, /see_caption, /del_caption
<b>Thumbnail:</b> /viewthumb, /delthumb

Optional: /cancel stops the current media job.
For help, contact @TANJIROKAMADO404."""
