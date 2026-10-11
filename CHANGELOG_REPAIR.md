# Repair Changelog

## Runtime and deployment

- **`bot.py`** — Pins startup to the repository root, pre-imports plugins with full tracebacks, reports discovered and post-start handler counts, refuses zero-handler startup, and honors `WEBHOOK` so worker deployments can skip the optional HTTP health server.
- **`config.py`** — Preserves the existing environment-variable names, adds optional `ENCODE_RESOLUTIONS` and `FFMPEG_TIMEOUT` controls, rejects unsupported resolutions and non-positive FFmpeg timeouts, and includes `/about` copy.
- **`Dockerfile` and `render.yaml`** — The Render Blueprint now selects the existing Dockerfile, which installs FFmpeg and launches `python3 bot.py`; it also exposes the optional encoding and timeout variables. No live Render settings were changed.
- **`RENDER_DEPLOYMENT.md`** — Documents the verified deployment configuration, required environment, opt-in encoding, and production verification boundaries.
- **`ROOT_CAUSE_REPORT.md`** — Separates the confirmed Render Python-versus-Docker/FFmpeg mismatch from the still-unproven production command-silence cause, and lists the exact redacted Render evidence needed to distinguish startup, database, and update-delivery failures.
- **`README.md`** — Corrects the concurrency claim and documents the health toggle, optional encoding, FFmpeg runtime requirement, and `/cancel`.

## Plugin behavior

- **`plugins/start_&_cb.py` → `plugins/start_and_callbacks.py`** — Renamed to an ordinary Python module name; adds working `/help` and `/about` commands and limits menu callbacks to their own data values.
- **`plugins/thumb_&_cap.py` → `plugins/thumbnail_caption.py`** — Renamed to a conventional Python module name; existing thumbnail and caption commands are retained.
- **`plugins/auto_rename.py`** — Uses Pyrogram's parsed command arguments for formats with spaces/braces and validates `/setmedia` values.
- **`plugins/file_rename.py`** — Provides path-safe template rendering, per-user job isolation, generated output variants when configured, safe metadata remux/encoding, thumbnail normalization, flood-wait handling, user-visible errors, and guaranteed cleanup. It shows the requested progress bar during Telegram transfers and FFmpeg work, preserves the intended upload filename, and now stops active Telegram downloads/uploads when cancellation is requested.
- **`plugins/force_subs.py`** — Runs subscription checks at an earlier handler priority and only handles its own subscription callback.
- **`plugins/admin_panel.py`** — Reports tutorial failures via logging and a user-visible response instead of a silent print.
- **`plugins/cancel.py`** — `/cancel` requests safe cancellation of the active download, FFmpeg process, or upload.

## Shared helpers and storage

- **`helper/__init__.py`, `plugins/__init__.py`** — Make the module roots explicit Python packages.
- **`helper/filename.py`** — Parses common episode/quality filename conventions, substitutes legacy/current template markers, and sanitizes file basenames.
- **`helper/ffmpeg_tools.py`** — Builds shell-free FFmpeg argument lists for metadata and H.264 encodes; encoding selects the first normal video stream, excludes attached cover art, and preserves audio, subtitles, and attachments. The x264 preset is `ultrafast` with CRF 26; the speed/file-size tradeoff is documented. It also parses FFmpeg progress, probes duration, and supports process timeout/cancellation.
- **`helper/progress.py`** — Formats a throttled Telegram progress bar with byte/speed/ETA for transfers and percentage/output-size/realtime-speed/ETA for media processing.
- **`helper/job_control.py`** — Tracks in-memory per-user cancellation events.
- **`helper/database.py`** — Keeps existing fields/defaults and uses non-destructive upserts for preferences, avoiding first-use failures and Mongo update-path conflicts.

## Regression coverage

- **`tests/test_config.py`** — Rejects a zero FFmpeg timeout without external services.
- **`tests/test_health_toggle.py`** — Verifies the `WEBHOOK` setting starts or skips the health server without contacting Telegram.
- **`tests/test_helpers.py`** — Filename parsing/sanitization, FFmpeg argument construction, and subprocess cancellation.
- **`tests/test_database.py`** — Mocked Mongo upsert behavior and preservation of existing user data.
- **`tests/test_media_handler.py`** — Mocked media download/rename/caption/upload, active transfer cancellation, and temporary-file cleanup; no Telegram or Mongo connection.
- **`tests/test_plugin_registration.py`** — Pyrogram 2.0.80 plugin loading, group counts, command parsing, callback isolation, non-repository startup directory, and early-snapshot timing.
- **`tests/test_ffmpeg_integration.py`** — Generated-video tests for supported profiles, metadata remux, and attached-cover multistream behavior, including matched-time frame and audio checks.
- **Progress regression coverage** — Confirms the requested progress layout, Pyrogram transfer callback wiring, FFmpeg progress parsing, and real progress output from a generated sample clip.

## Scope and limits

- The uploaded source copy was audited and repaired. No live GitHub repository, Render dashboard, Telegram bot, or production MongoDB was accessed or changed.
- The Docker image was not built because Docker is unavailable in the sandbox. Live Telegram delivery, production MongoDB operations, and a Render deploy remain unverified.
