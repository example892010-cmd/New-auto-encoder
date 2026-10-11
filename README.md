## Auto Rename Bot With Metadata Rename


##  Configurations

- `BOT_TOKEN` - Get the bot token from [@BotFather](https://t.me/BotFather).
- `API_ID` - Obtain from [my.telegram.org](https://my.telegram.org).
- `API_HASH` - Obtain from [my.telegram.org](https://my.telegram.org).
- `ADMIN` - Bot controllers' IDs, use space to split multiple IDs.
- `LOG_CHANNEL` - Bot log sending channel. **Note:** ID must start with `-100`.
- `DB_URL` - MongoDB URL from [MongoDB Atlas](https://cloud.mongodb.com).
- `DB_NAME` - Your MongoDB database name. **Optional**.
- `FORCE_SUB_CHANNELS` - Your force subscription channel usernames without `@`. **Optional**. Use format `1CHANNEL,2CHANNEL`.
- `START_PIC` - Start message photo. **Optional**.
- `WEBHOOK` - Enable the optional HTTP health endpoint. Keep it `True` for Render web services; set it to `False` only when running as a worker. **Optional**.
- `ENCODE_RESOLUTIONS` - Optional comma-separated output profiles: `480`, `720`, and/or `1080`. Leave unset to disable transcoding. FFmpeg is installed by the included Dockerfile.
- `FFMPEG_TIMEOUT` - Positive maximum runtime for each FFmpeg process in seconds; defaults to `1800`. **Optional**.

For Render deployments that need metadata or video encoding, use the Docker runtime configured in `render.yaml`; the Dockerfile installs FFmpeg.

## Deploy to Koyeb

<a target="_blank" href="https://app.koyeb.com/deploy?type=git&repository=github.com/AshutoshGoswami24/Auto-Rename-Bot&branch=main&name=ashu-rename-bot">
  <img src="https://www.koyeb.com/static/images/deploy/button.svg" alt="Deploy to Koyeb" style="width:170px;">
</a>

## Deploy to Heroku

<a href="https://heroku.com/deploy?template=https://github.com/AshutoshGoswami24/Auto-Rename-Bot">
  <img src="https://www.herokucdn.com/deploy/button.svg" alt="Deploy to Heroku" style="width:170px;">
</a>

## Deploy to Cloud Shell Editor

<a target="_blank" href="https://shell.cloud.google.com/cloudshell/open?cloudshell_git_repo=https://github.com/AshutoshGoswami24/Auto-Rename-Bot&tutorial=Ashu/g-cloud.md">
  <img src="https://raw.githubusercontent.com/AshutoshGoswami24/text-leech-bot/main/.github/img/x.svg" alt="Deploy to Cloud Shell Editor" style="width:170px;">
</a>

## 🥰 Features

- Renames files very fast.
- Permanent thumbnail support.
- Force join for the user to use the bot.
- Supports broadcasts.
- Custom caption support.
- Custom start-up picture.
- Force subscription available.
- Processes one media job per user at a time; different users can work concurrently.
- Deploy to Koyeb, Heroku, and Railway.
- Automatically rename your files.
- Set media type to upload file type.
- METADATA add with rename.
- Optional H.264 resolution encoding (480p, 720p, or 1080p).

### 🚦 User Commands

```
start - Check if the bot is running.
autorename - To auto rename your files.
tutorial - SETUP AUTO RENAME FORMAT 
setmedia - To set your media type preference.
metadata - to set metadata
viewthumb - To view current thumbnail.
delthumb - To delete current thumbnail.
set_caption - set a custom caption.
see_caption - see your custom caption.
del_caption - delete custom caption.
cancel - Stop the active download, encoding, or upload.
restart - To restart the bot [FOR ADMINS USE ONLY]
broadcast - Message Broadcast command [FOR ADMINS USE ONLY].
status - Check bot status [FOR ADMINS USE ONLY].
```

## Connect with Me

<p align="center">
<a href="https://t.me/AshutoshGoswami24">
  <img src="https://img.shields.io/badge/-Asʜᴜᴛᴏsʜ Gᴏsᴡᴀᴍɪ 𝟸𝟺 🇮🇳™-0077B5?style=flat&logo=Telegram&logoColor=white"/>
</a>
<a href="https://t.me/AshuSupport">
  <img src="https://img.shields.io/badge/-Ashu Support-0077B5?style=flat&logo=Telegram&logoColor=white"/>
</a>
</p>

---

Credits: 🎖️ [𝗔𝘀𝗵𝘂𝘁𝗼𝘀𝗵𝗚𝗼𝘀𝘄𝗮𝗺𝗶𝟮𝟰](https://github.com/AshutoshGoswami24) 🤖

_Last Edited on: 08/21/2024, 10:12:42 AM_
