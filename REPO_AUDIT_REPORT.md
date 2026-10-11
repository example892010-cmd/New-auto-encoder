# Repository Audit Report

## Findings fixed

1. **Render could start without FFmpeg.** The uploaded `render.yaml` selected native Python, while the repository's Dockerfile installs the FFmpeg binary needed by metadata remuxing and configured encoding. The Blueprint now selects the Docker runtime and exposes `ENCODE_RESOLUTIONS` and `FFMPEG_TIMEOUT`. Encoding remains opt-in; an unset resolution variable means no transcoding.
2. **`/cancel` did not stop an active Telegram transfer.** It set a cancellation event, but download and upload callbacks did not invoke Pyrogram's transfer-stop mechanism. The active download/upload callbacks now stop transmission when the event is set, and cancellation still reaches the existing FFmpeg cancellation/cleanup path.
3. **The `WEBHOOK` option was parsed but ignored.** Startup now creates the health endpoint only when enabled. The Render web-service Blueprint sets it to `True`; worker deployments can set it to `False`.
4. **A zero/negative FFmpeg timeout could make every subprocess fail immediately.** Configuration now rejects non-positive values at startup.
5. **Repository guidance had drifted.** The deployment note named `veryfast` although the current encoder uses `ultrafast`, and the README claimed unlimited concurrent processing despite one active job per user. Those descriptions are corrected.

## Validation

The uploaded project test suite passed **31/31 tests** under Python 3.10.21 and 3.12.3. Ruff's undefined-name/unused-import checks, compilation under both runtimes, local FFmpeg/ffprobe integration tests, and Render YAML parsing passed. New regressions use mocks to exercise transfer-stop behavior and the WEBHOOK health-server toggle, verify temporary-file cleanup, and reject invalid timeout configuration.

## Remaining limits

Docker was unavailable, so the Docker image was not built. No Telegram API session, production MongoDB, GitHub repository, or Render service was accessed. Accordingly, this audit does **not** prove the bot is fully working in production. Live delivery, credentials, database networking, Render build/start, and the exact user video remain unverified. The user must set `ENCODE_RESOLUTIONS` in Render to enable transcoding; the repository intentionally does not enable costly encoding by default.

The archive prepared for delivery contains only files modified or added in this audit, with repository-relative paths. It does not contain a second copy of the complete repository.

## Deployment references

- [Render Blueprint YAML reference](https://render.com/docs/blueprint-spec)
- [Docker on Render](https://render.com/docs/docker)
