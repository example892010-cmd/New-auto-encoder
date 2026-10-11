# Root-Cause Report — Auto-Rename Bot

## Finding

The supplied repository snapshot does **not** establish the exact production reason that the bot stopped responding. The live Render process logs, deployed commit, and environment-variable presence are not part of the ZIP, and no live service was accessed. It would be misleading to call the empty handler-count snapshot the proven root cause.

One concrete deployment mismatch **is** established from the repository: the original `render.yaml` selected Render's native Python runtime (`env: python`) and a pip build command, while FFmpeg was installed only by the project's Dockerfile. A Render deployment following that Blueprint would not reliably have the FFmpeg executable required for metadata remuxing and optional video encoding. This explains FFmpeg/media-processing failures, but it does **not by itself explain why `/start` or other commands receive no reply**. The Blueprint has been corrected to select the Docker runtime.

## What was verified from the source and tests

- With the declared Pyrogram 2.0.80 dependency and placeholder-only configuration, all plugins import and the loader registers **29 handlers**: 2 in group `-1` and 27 in group `0`. The local test exercises plugin preflight, the Pyrogram loader, required command decorators, command parsing, and callback scoping without connecting to Telegram.
- Pyrogram's plugin loader schedules handler additions on the event loop. A dispatcher count read immediately after plugin discovery can be `{}` before those scheduled additions run. The test reproduces the empty early snapshot and then observes the nonzero handler groups after yielding to the loop. Therefore, an empty count is evidence only if its timing relative to startup is known.
- The repository had a relative plugin root, which could point to the wrong directory if Render starts the process elsewhere. Startup now resolves the root from `bot.py`, changes to that directory, imports each plugin with a full traceback on error, and checks registered counts after client startup.
- Root-level legacy modules coexist with `plugins/`, but the active client explicitly loads `plugins` as its Smart Plugins root. The duplicate root modules are not loaded by that configured discovery path, so they are not demonstrated to cause duplicate handler registration.
- Mongo calls are generally caught and logged in the helper layer; a failed preference read falls back to a default rather than blocking every handler. Startup still requires `DB_URL`, and the database client is initialized at import. A missing/invalid value or a live connection failure can be diagnosed only from the deployment's actual startup/database logs.

## Changes made in the repair

The Render Blueprint now uses the Dockerfile that installs FFmpeg; plugin discovery is pinned to the project root and reports both preflight and post-start handler counts; the health endpoint now follows `WEBHOOK`; callbacks are scoped; missing help/about routes were added; database preference updates use safe non-destructive upserts; `/cancel` stops active Telegram transfers and FFmpeg work; and media workflows include tested temporary-file cleanup and user-visible failure reporting. See `CHANGELOG_REPAIR.md` for the file-by-file list and `TEST_REPORT.md` for exact checks.

## Render evidence needed to identify the production-only cause

From Render, provide the following **redacted** information; do not share tokens, API hashes, Mongo URIs, or other secret values:

1. The deployment Events entry showing the deployed commit and whether the service was built as Docker or native Python.
2. The startup Logs from process launch through either the first successful startup or process exit. Relevant lines include `Set API_ID, API_HASH, BOT_TOKEN, and DB_URL...`, any traceback, `Plugin import failed`, each `Plugin preflight OK`, `Plugin preflight handler counts by group`, `Pyrogram registered handler counts by group`, and `started successfully`.
3. Any MongoDB errors, especially `Could not read...`, `ServerSelectionTimeoutError`, or authentication/network failures, with secret values removed.
4. If startup succeeds but users still get no response, a short log window around a test `/start`, plus confirmation that the test targeted the deployed bot username and that Render shows the service as Live. Pyrogram's normal log level may not print every inbound message, so absence of an update line alone is not proof that Telegram sent none.
5. Confirm whether `BOT_TOKEN`, `API_ID`, `API_HASH`, and `DB_URL` are configured (yes/no only), and whether BotFather privacy/group settings are relevant to where the command was sent.

These observations distinguish a startup/configuration failure, a plugin/import/runtime mismatch, database trouble, and an update-delivery/targeting issue. Until they are available, the exact cause of the live no-response symptom remains unverified.

## Limits

No live Render service, GitHub repository, Telegram session, or production MongoDB was contacted or changed. The passing local tests establish offline behavior only; they do not prove production is working. Docker was unavailable, so the image itself was not built. The exact deployed state must still be checked against the repaired source and verified using the redacted Render log lines above.
