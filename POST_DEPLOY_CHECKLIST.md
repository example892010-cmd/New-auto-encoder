# Post-Deploy Verification Checklist

Run these steps after **you** deploy the repaired revision; no production action was taken as part of this repair.

- [ ] Confirm Render is running the expected repository commit.
- [ ] Confirm required environment values exist: `BOT_TOKEN`, `API_ID`, `API_HASH`, and `DB_URL` (do not paste values into logs or chat).
- [ ] Confirm the service start command is `python3 bot.py`.
- [ ] If metadata or encoding is required, confirm the selected runtime is Docker from the included Dockerfile and `ffmpeg -version` works.
- [ ] Confirm logs show plugin preflight and post-start counts of `{-1: 2, 0: 27}`, followed by a successful bot-start line.
- [ ] Send `/start`, `/help`, and `/about`; confirm each replies.
- [ ] Set a format with `/autorename {title} S{season} EP{episode} [{quality}]` and a media output with `/setmedia document` (or `video`/`audio`).
- [ ] Send one small test file; verify its name/caption, output type, and no extra duplicate quality marker.
- [ ] If enabled, test one short video with `ENCODE_RESOLUTIONS=720` first; only then add other profiles.
- [ ] Check that the bot reports FFmpeg errors clearly, `/cancel` cancels an active processing job, and Mongo user preferences remain present.
- [ ] Review Render logs for startup/import tracebacks and resource/timeouts before sending larger files.

If the handler count is still zero **after** `Client.start()` finishes, compare the deployed commit and runtime working directory with the log and send the first import traceback/startup lines to the maintainer. A pre-start empty snapshot alone is not evidence of a failed plugin load.