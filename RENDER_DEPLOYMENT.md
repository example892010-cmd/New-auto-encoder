# Render Deployment Notes

## Checked-in deployment configuration

The repository's `render.yaml` now selects Render's Docker runtime and builds the root `Dockerfile`. This is required for predictable FFmpeg-backed metadata remuxing and resolution encoding: the Dockerfile installs the FFmpeg executable, while a native Python runtime does not guarantee it. The container starts with `python3 bot.py` from the Dockerfile's `CMD`. Render's Blueprint reference documents `runtime: docker` and Dockerfile-based services: [Blueprint YAML reference](https://render.com/docs/blueprint-spec) and [Docker on Render](https://render.com/docs/docker).

The Blueprint sets `WEBHOOK=True` so the Render web service binds its health endpoint. The application now honors `WEBHOOK=False` if it is run as a worker without an HTTP health route. The checked-in file does not contain production credentials. No live Render service, GitHub repository, or MongoDB settings were accessed or changed.

## Environment variables

Set secrets in Render's Environment page; never commit them to the repository.

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
| `WEBHOOK` | No | Health endpoint toggle; defaults to `True`; keep `True` for this Render web service |
| `ENCODE_RESOLUTIONS` | No | Optional comma-separated profiles: `480`, `720`, `1080` |
| `FFMPEG_TIMEOUT` | No | Positive per-process timeout in seconds; defaults to `1800` |

## Encoding behavior

Leave `ENCODE_RESOLUTIONS` unset to run rename and metadata-remux operations without transcoding. Set `ENCODE_RESOLUTIONS=720` for one 720p output, or `ENCODE_RESOLUTIONS=480,720,1080` for the three requested profiles. The blueprint prompts for this optional value; it does not enable transcoding by default.

Encoding uses H.264 (`libx264`) with the `ultrafast` preset and CRF 26. It copies audio, subtitles, and attachments, selects the first normal video stream rather than attached cover art, and caps output height without upscaling. The faster preset can increase file size; CRF remains unchanged, but this does not guarantee pixel-identical output.

## Post-deploy checks

Confirm the deployed commit and required environment variables, then check logs for plugin preflight and registered handler counts similar to `{-1: 2, 0: 27}`. Test `/start`, `/help`, `/about`, `/autorename`, `/setmedia`, and `/cancel`. Send one small file and one short video. If encoding is enabled, verify one configured profile first, then test additional profiles. Confirm `/cancel` stops an active download, encoding process, or upload and removes temporary files.

The local regression suite passed in Python 3.10 and 3.12, but the Docker image, live Telegram API, production MongoDB, and Render deployment were not run from this audit. Successful local checks therefore do not prove the production service is fully working.
