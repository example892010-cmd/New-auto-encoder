# Root-Cause Report — Auto-Rename Bot

## Executive finding

The reported `Registered Pyrogram handler counts by group: {}` is **not reproducible as a steady-state result from the inspected repository**. Under Pyrogram **2.0.80**, a clean dependency installation, placeholder configuration, and no Telegram/MongoDB connection, the original repository's plugins could be imported and its handlers loaded. The repaired tree loads **29 handlers**: **2 in group `-1`** and **27 in group `0`**.

The exact production cause cannot be proven from the repository snapshot alone: the inspected `bot.py` did not contain the reported custom log line, and I did not access or modify the live Render service. The strongest verified explanation for an empty `{}` snapshot is **reading `dispatcher.groups` immediately after Pyrogram's synchronous plugin-discovery call but before its scheduled handler-addition tasks have run**. The Pyrogram 2.0.80 loader creates asynchronous dispatcher tasks; without yielding to the event loop, the groups dictionary is empty. The regression test demonstrates both states: an immediate snapshot is `{}`, then after the loop processes the queued additions the actual count is `{-1: 2, 0: 27}`.

If Render logged the count only after `Client.start()` had fully completed, the more likely explanation is instead a **deployment/runtime mismatch** (for example, a different commit or plugin root/working directory). The available evidence does not distinguish those production possibilities conclusively.

## Evidence collected

1. **The old plugin tree was not missing handlers.** A local Pyrogram 2.0.80 import/load test found 26 decorated handlers in the checked-out version before the repair. The reference repository was inspected for comparison, but it is a separate video-encoding bot and does not explain this Render count.
2. **The displayed empty count can be a timing artifact.** In Pyrogram 2.0.80, `Dispatcher.add_handler()` schedules an async task on the loop. A count read before the loop yields can therefore be `{}` even though the loader has discovered the plugins.
3. **The supplied log text was not present in the checked-out source.** That means the log line came from another revision, a local/deployment-only diagnostic, or an external wrapper; its exact execution point is not available here.
4. **The original plugin names containing `&` are undesirable but not proven to be the root cause.** They were renamed to conventional importable names, but the old names did not, by themselves, reproduce a zero-handler result in the inspected loader test.
5. **A relative plugin root was a genuine deployment fragility.** Pyrogram was configured with `plugins={"root": "plugins"}`. If the process working directory differed from the repository root, plugin discovery could inspect the wrong directory. Startup now anchors the process to the absolute repository path and preflights every module before connecting.

## Other verified behavior defects repaired

These do not, by themselves, prove why the handler count was empty, but they could make a running bot look non-responsive or produce failed media jobs:

- `/help` and `/about` were displayed in the help text without actual message handlers.
- A callback handler matched **every** callback query and could answer/consume metadata and force-subscription button actions.
- FFmpeg metadata arguments were assembled with a nested-loop/list mutation pattern rather than flat option/value argument pairs.
- Media processing lacked isolated per-job temporary directories, safe filename sanitization, clear FFmpeg failure reporting, and a user cancellation path.
- Preference updates did not use a safe upsert pattern for users who had not previously run `/start`; the replacement preserves defaults and does not reset existing records.
- Tutorial errors were printed rather than logged with a traceback or reported to the user.

## Remediation in this delivery

- Resolve the project and plugin directories from `bot.py`'s absolute path; pin the process working directory before plugin discovery.
- Import every plugin before connecting. On failure, log the full traceback and abort instead of appearing healthy with missing handlers.
- Record preflight counts and **post-start dispatcher counts** only after startup has completed; abort on zero registered handlers.
- Use explicit Python package markers and conventional plugin filenames.
- Scope callback filters and add the missing commands.
- Add tested filename parsing, media metadata/encoding command builders, safe temp-file handling, timeout/cancel support, and optional 480p/720p/1080p encodes.

## What remains unverified

No live Render logs, active Render settings, production Telegram bot token, or production MongoDB credentials were accessed. I therefore did not claim a live deploy passed, and I did not change GitHub, Render, bot credentials, or production data. To discriminate timing from a deployed-code/path mismatch, compare the Render deployment commit with this source and inspect whether the empty-count diagnostic runs before or after `await super().start()` completes.