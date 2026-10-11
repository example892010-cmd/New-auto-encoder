# Test Report

## Result

**23 tests passed; 0 failed; 0 skipped** under both Python **3.10.21** and **3.12.3**. The Python 3.10 run used the repository's complete `requirements.txt`, including `TgCrypto`. Ruff's undefined-name/unused-import checks and Python compilation both passed. FFmpeg and ffprobe were available in the sandbox.

## Executed checks

From `/home/ubuntu/work/auto-rename-bot`:

```bash
DB_URL='mongodb://127.0.0.1:27017' \
DB_NAME=autorename_test API_ID=12345 API_HASH=test-hash BOT_TOKEN='123456:TEST' \
/tmp/autorename-venv/bin/python -m unittest discover -s tests -v
```

Outcome: `Ran 23 tests ... OK` on Python 3.10.21 and again on Python 3.12.3.

```bash
/tmp/autorename-venv/bin/python -m compileall -q -f .
```

Outcome: **PASS**.

```bash
uvx --from ruff ruff check --select F bot.py config.py helper plugins tests
```

Outcome: **PASS** after removing the two unused imports reported on the first run.

The values above were non-production placeholders. Test code mocks Telegram operations and the Mongo collection; it does not connect to a live bot, MongoDB, or Render.

## Coverage and concrete outcomes

| Area | Result |
|---|---|
| Pyrogram 2.0.80 plugin import/load | **PASS** — 29 actual handlers loaded |
| Handler group counts | **PASS** — `{-1: 2, 0: 27}` after queued registrations run |
| Empty early snapshot timing | **PASS** — immediate pre-yield snapshot can be `{}`, then becomes `{-1: 2, 0: 27}` |
| Working-directory recovery | **PASS** — preflight started from `/tmp` anchors to the repository plugin folder |
| `/help`, `/about`, `/autorename`, `/setmedia`, `/metadata` filters | **PASS**, including `/autorename@aniflix_bot ...` argument parsing |
| Metadata/subscription callback isolation | **PASS** — those callbacks do not match the menu handler |
| Filename parsing and sanitization | **PASS** — SxxExx, EPx, dotted names, quality, path safety, and template substitution |
| Mongo persistence | **PASS** — mocked upserts do not conflict on fields or remove stored preferences |
| Mocked Telegram media path | **PASS** — rename, caption, upload call, active-job cleanup, and temporary-directory cleanup |
| Metadata-remux upload name | **PASS** — verifies the externally uploaded filename remains the user's requested output name |
| Initial status-send failure | **PASS** — confirms the user's active-job lock is cleared |
| FFmpeg argument safety | **PASS** — flat metadata option/value pairs; no shell interpolation |
| Generated sample encoding | **PASS** — 480p, 720p, and 1080p encode commands executed; a 640×360 input remained 640×360 (no upscaling) |
| Metadata remux | **PASS** — sample output retains the regression title |
| FFmpeg timeout and cancellation | **PASS** — test child processes were terminated on both timeout and user-cancel events |
| Python source compilation | **PASS** |

## Limits

- Python 3.10.21 was explicitly provisioned, all declared dependencies were installed into an isolated environment, and all tests passed there. The Docker image itself was not built because Docker is not available in the sandbox.
- No live Telegram API/bot token, production MongoDB, or Render deployment was used. This report therefore proves local loader/helper/media behavior, not live network behavior or a production rollout.
