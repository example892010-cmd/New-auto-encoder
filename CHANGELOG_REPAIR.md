# Repair Changelog

## Runtime and configuration

- **`bot.py`** — Pins startup to the repository root, pre-imports plugins with full tracebacks, reports discovered and post-start handler counts, refuses zero-handler startup, and treats the health route/admin notifications as optional.
- **`config.py`** — Preserves existing environment names and adds optional `ENCODE_RESOLUTIONS` (`480`, `720`, `1080`) and `FFMPEG_TIMEOUT` controls, plus explicit `/about` copy.
- **`Dockerfile`** — Uses Python 3.10 slim, installs FFmpeg and compiler tools needed for the declared dependencies, and starts with `python3 bot.py`.

## Plugin behavior

- **`plugins/start_&_cb.py` → `plugins/start_and_callbacks.py`** — Renamed to an ordinary Python module name; adds working `/help` and `/about` commands and limits menu callbacks to their own data values.
- **`plugins/thumb_&_cap.py` → `plugins/thumbnail_caption.py`** — Renamed to a conventional Python module name; existing thumbnail and caption commands are retained.
- **`plugins/auto_rename.py`** — Uses Pyrogram's parsed command arguments for formats with spaces/braces and validates `/setmedia` values.
- **`plugins/file_rename.py`** — Adds path-safe template rendering, per-user job isolation, generated output variants when configured, safe metadata remux/encoding, thumbnail normalization, timeout/cancel support, flood-wait handling, user-visible errors, and guaranteed cleanup. Remuxes keep the intended Telegram upload filename, optional-thumbnail failures do not block uploads, and a failed initial status reply no longer strands the user's busy lock or temp directory.
- **`plugins/force_subs.py`** — Runs subscription checks at an earlier handler priority and only handles its own subscription callback.
- **`plugins/admin_panel.py`** — Reports tutorial failures via logging and a user-visible response instead of a silent print.
- **`plugins/cancel.py`** — Adds `/cancel` for the active media job.

## Shared helpers and storage

- **`helper/__init__.py`, `plugins/__init__.py`** — Make the module roots explicit Python packages.
- **`helper/filename.py`** — Parses common episode/quality filename conventions, substitutes legacy/current template markers, and sanitizes file basenames.
- **`helper/ffmpeg_tools.py`** — Builds shell-free FFmpeg argument lists for metadata and H.264 encodes; supports process timeout and cancellation.
- **`helper/job_control.py`** — Tracks in-memory per-user cancellation events.
- **`helper/database.py`** — Keeps existing fields/defaults and uses non-destructive upserts for preferences, avoiding first-use failures and Mongo update-path conflicts.

## Regression coverage

- **`tests/test_helpers.py`** — Filename parsing/sanitization, FFmpeg argument construction, and subprocess cancellation.
- **`tests/test_database.py`** — Mocked Mongo upsert behavior and preservation of existing user data.
- **`tests/test_media_handler.py`** — Mocked media download/rename/caption/upload and temp cleanup, with no Telegram or Mongo connection.
- **`tests/test_plugin_registration.py`** — Pyrogram 2.0.80 plugin loading, group counts, command parsing (including bot mentions), callback isolation, non-repository startup directory, and early-snapshot timing.
- **`tests/test_ffmpeg_integration.py`** — Generates a short test video and validates all supported profiles plus metadata remux using the installed FFmpeg/ffprobe.

## Deliberately not changed

- The live GitHub repository/branch and Render dashboard settings were not modified.
- `render.yaml` remains the existing Python-runtime blueprint. The deployment note recommends selecting the included Dockerfile when FFmpeg-backed metadata/encoding is required; the live Render runtime was not switched.
- Existing secrets, MongoDB data, bot identity, channel links, and branding were not replaced.
