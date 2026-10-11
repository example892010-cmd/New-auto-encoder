# Test Report

## Results

**31 tests passed; 0 failed; 0 skipped** under Python **3.10.21** and **3.12.3**. Ruff's undefined-name/unused-import checks and source compilation passed. The checked-in `render.yaml` parsed successfully and contains the Docker runtime plus the optional encoding and timeout environment variables.

## Executed checks

The full suite was run from the uploaded repository copy with placeholder-only environment values:

```bash
DB_URL='mongodb://127.0.0.1:27017' \
DB_NAME=autorename_test API_ID=12345 API_HASH=test-hash BOT_TOKEN='123456:TEST' \
/tmp/autorename310/bin/python -m unittest discover -s tests -v

DB_URL='mongodb://127.0.0.1:27017' \
DB_NAME=autorename_test API_ID=12345 API_HASH=test-hash BOT_TOKEN='123456:TEST' \
/tmp/autorename-venv/bin/python -m unittest discover -s tests -v
```

Both runs reported `Ran 31 tests ... OK`. Unit tests mock Telegram calls and Mongo collections; the integration tests generate synthetic media and execute local FFmpeg/ffprobe.

Additional checks:

```bash
uvx --from ruff ruff check --select F bot.py config.py helper plugins tests
/tmp/autorename310/bin/python -m compileall -q -f bot.py config.py route.py helper plugins tests
/tmp/autorename-venv/bin/python -m compileall -q -f bot.py config.py route.py helper plugins tests
```

All passed. `render.yaml` was parsed with PyYAML and checked for `runtime: docker`, absence of a native-only `buildCommand`, and the optional encoding/timeout variables.

## Coverage highlights

- Pyrogram 2.0.80 plugin import and registration: **PASS** — 29 handlers loaded; group counts `{-1: 2, 0: 27}` after registrations complete.
- Filename parsing, template replacement, and path sanitization: **PASS**.
- Mongo user preference upsert behavior: **PASS** using mocks.
- Mocked media rename/caption/upload and temporary-file cleanup: **PASS**.
- `/cancel` during a Telegram download and during an upload: **PASS** in mocks that exercise Pyrogram's documented `stop_transmission` callback mechanism; the job lock and temporary files were cleaned in both cases.
- `WEBHOOK` health endpoint toggle: **PASS** — mocked bot startup skips the server when disabled and starts it when enabled, without connecting to Telegram.
- FFmpeg command construction and timeout/cancellation: **PASS**.
- Synthetic video encoding at configured profiles, metadata remuxing, and the attached-cover multistream regression: **PASS**. The regression verifies that the encoder selects the normal video stream, preserves audio, and keeps a matching-time frame within its test threshold.
- Progress display and transfer callbacks: **PASS**.
- Invalid zero FFmpeg timeout: **PASS** — rejected at configuration import with an actionable error.
- Render YAML syntax and expected Docker configuration: **PASS**.

The earlier synthetic preset benchmark remains illustrative, not a production benchmark: with CRF unchanged at 26, `ultrafast` completed a 10-second synthetic 1280×720 clip in 0.569s versus 1.079s for `veryfast`, while the output increased from 2.04 MB to 7.25 MB. Faster encoding trades compression efficiency for speed and does not guarantee pixel-identical output.

## Not verified

- Docker was unavailable in the sandbox, so the image itself was not built.
- No live Telegram bot/token, production MongoDB, GitHub repository, or Render service was accessed. The test results prove offline regression behavior, not live production operation.
- The exact user-provided video mismatch remains unverified because the original and processed video files were not included in the repository attachment.
- Encoding remains opt-in. If `ENCODE_RESOLUTIONS` is unset in Render, video transcoding does not run; set a profile explicitly to enable it.
