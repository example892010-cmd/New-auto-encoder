# Frame-Preservation Investigation

## Finding

The encoding command used `-map 0`, which selects **every** input stream. That includes attached cover-art/thumbnail streams represented by FFmpeg as video streams. The command then applies the scaling filter and H.264 encoder to every mapped video stream, so cover art can become an additional ordinary video track in the output. A player can select or preview a different track than the intended moving video.

This is a confirmed stream-selection defect in the pipeline. It is a plausible explanation for a player showing different imagery, but it is **not confirmed as the cause of the reported basket-to-court discrepancy**: the original and processed user videos and referenced screenshots were not present in the attachments, so they could not be compared.

## Pipeline inspection

- The bot downloads Telegram media to a job-specific temporary directory. The filename change uses `os.replace` on that downloaded temporary copy; it does not modify the Telegram original.
- Encoding reads the renamed temporary copy and writes each rendition to a unique path in the same job directory. The output is added to the upload list only after FFmpeg succeeds and the output file exists.
- Thumbnail preparation downloads/resizes a separate image and passes it to Pyrogram as the upload's `thumb` parameter. It is not added to the FFmpeg filter graph or video frames.
- The only video filter is the resolution cap (`scale=-2:min(ih\,N)`), which preserves aspect ratio and does not upscale. No crop, overlay, alternate input, or frame replacement is performed.
- Metadata remux uses stream copy and does not re-encode or filter video frames.

## Code change

The H.264 encode command now maps `0:V:0`—the first non-attached video stream—rather than all streams, then maps optional audio, subtitles, and attachments separately. Audio remains stream-copied (`-c:a copy`), preserving its timing relative to the encoded video. FFmpeg's normal autorotation behavior and the existing aspect-ratio-preserving scale filter remain in place.

## Regression reproduction and verification

The new FFmpeg integration test creates a synthetic MP4 with a moving test scene, a distinct attached cover image, and AAC audio. With the legacy all-stream mapping, the encoded MKV contains two video streams. With the corrected mapping, it contains only the real moving-video stream. The test compares source and output frames at the same timestamp, checks that the mean absolute pixel difference stays below the regression threshold, and checks the copied audio codec and start time.

The full suite also runs all three configured resolution profiles and verifies that a 640×360 source is not upscaled.

## Remaining limitation

The attached text described the expected visuals but did not contain the actual video files or screenshots. Therefore, this report does not claim that the exact user-provided visual mismatch has been reproduced or conclusively attributed. Comparing the actual videos at matching timestamps and checking their stream layouts remains necessary to confirm whether the source had an attached/secondary video track or whether the screenshots came from different timestamps/files.
