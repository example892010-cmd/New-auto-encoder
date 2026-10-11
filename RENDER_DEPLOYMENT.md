# Render Deployment Notes

## Deployment settings were not changed

The live Render service and the GitHub repository were not accessed or modified. The existing `render.yaml` is left unchanged. It currently declares a native Python service with start command `python3 bot.py`.

## Recommended runtime when metadata/encoding must work

Use Render's **Docker** runtime with this repository's `Dockerfile`. It installs FFmpeg and starts the bot with:

```bash
python3 bot.py
```

The existing native Python blueprint may not provide the `ffmpeg` executable. Filename renaming can still work without FFmpeg, but metadata remux and configured encodes require it. The bot falls back to the renamed original if metadata remux fails; configured encode failures are shown to the user and logged.

If you choose to keep the native Python runtime, confirm `ffmpeg -version` is available in that Render environment before enabling metadata/encoding workflows. Do not assume the Docker image is in use just because a `Dockerfile` exists.

## Required and optional environment variables

Set the existing secrets in Render's Environment page; do not commit them to the repository:

| Variable | Required | Purpose |
|---|---:|---|
| `BOT_TOKEN` | Yes | Telegram bot token |
| `API_ID` | Yes | Telegram API ID |
| `API_HASH` | Yes | Telegram API hash |
| `DB_URL` | Yes | MongoDB connection URI |
| `DB_NAME` | No | Database name; defaults to `autorename` |
| `ADMIN` | No | Admin numeric IDs or usernames, comma/space separated |
| `LOG_CHANNEL` | No | Optional log channel ID |
| `FORCE_SUB_CHANNELS` | No | Comma-separated required channel usernames; legacy `FORCE_SUB` is also accepted |
| `START_PIC` | No | Optional Telegram file ID or URL |
| `PORT` | No | Health endpoint port; defaults to `8080` |
| `WEBHOOK` | No | Health endpoint toggle; defaults to `True` |
| `ENCODE_RESOLUTIONS` | No | Optional comma-separated profiles: `480`, `720`, `1080` |
| `FFMPEG_TIMEOUT` | No | Per-process timeout in seconds; defaults to `1800` |

No new secret is required. Existing environment-variable names remain supported.

### Encoding behavior

- Leave `ENCODE_RESOLUTIONS` unset to preserve the normal rename and metadata-remux workflow without transcoding.
- Set `ENCODE_RESOLUTIONS=720` for a single 720p rendition, or `ENCODE_RESOLUTIONS=480,720,1080` for three outputs per video.
- The encoder uses H.264 (`libx264`), `veryfast`, CRF 26, copies audio/subtitle streams, and caps height at the requested profile without upscaling.
- Non-video files do not enter the resolution-encoding loop.
- The Docker image includes FFmpeg; the native Python blueprint is not guaranteed to.

## Start command and first checks

The start command remains **`python3 bot.py`**. The container's `CMD` runs that same command.

On deployment, check the logs for lines similar to:

```text
Plugin preflight handler counts by group: {-1: 2, 0: 27}
Pyrogram registered handler counts by group: {-1: 2, 0: 27}
... started successfully ...
```

Do not use a handler-count snapshot taken before plugin-registration tasks have run. In Pyrogram 2.0.80, reading immediately after discovery can return `{}` even though handlers are queued for registration.

Then verify `/start`, `/help`, `/about`, set a filename with `/autorename {title} S{season} EP{episode} [{quality}]`, and send one small test file. If encoding is enabled, send a short video and verify each configured output. MongoDB must permit connections from the Render service; do not change database access rules blindly or expose credentials in logs.
