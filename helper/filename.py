"""Pure helpers for parsing source names and rendering safe output names."""
from __future__ import annotations

import os
import re
import unicodedata

_SEASON_EPISODE = re.compile(
    r"(?i)(?<![A-Z0-9])S(?P<season>\d{1,2})\s*(?:E|EP)\s*(?P<episode>\d{1,3})(?!\d)"
)
_SEASON_THEN_EPISODE = re.compile(
    r"(?i)(?<![A-Z0-9])S(?P<season>\d{1,2})\s*[-._ ]+\s*(?:E|EP)?\s*(?P<episode>\d{1,3})(?!\d)"
)
_EPISODE_ONLY = re.compile(r"(?i)(?<![A-Z0-9])(?:EP|E)\s*[-._ ]?\s*(\d{1,3})(?!\d)")
_QUALITY = re.compile(
    r"(?i)(?<![A-Z0-9])(?P<quality>2160\s*p|1440\s*p|1080\s*p|720\s*p|576\s*p|540\s*p|480\s*p|360\s*p|240\s*p|4\s*k|2\s*k|HD(?:TV)?|WEB[- .]?DL|Blu[- .]?Ray)(?![A-Z0-9])"
)
_INVALID = re.compile(r'[\\/:*?"<>|\x00-\x1f]')
_SPACE = re.compile(r"\s+")


def parse_filename(filename: str) -> dict[str, str]:
    """Extract title, season, episode and source quality from a media filename."""
    basename = os.path.basename(filename or "")
    stem = os.path.splitext(basename)[0]
    normalized = stem.replace("_", " ").replace(".", " ")

    match = _SEASON_EPISODE.search(normalized) or _SEASON_THEN_EPISODE.search(normalized)
    season = match.group("season") if match else "01"
    episode = match.group("episode") if match else None

    if not episode:
        ep_match = _EPISODE_ONLY.search(normalized)
        if ep_match:
            episode = ep_match.group(1)
        else:
            # Legacy names such as "Show - 02 - 1080p"; do not mistake a
            # resolution or a four-digit year for an episode number.
            simple = re.search(r"(?:^|\s)-\s*(\d{1,3})(?=\s|$)", normalized)
            if simple:
                episode = simple.group(1)

    quality_match = _QUALITY.search(normalized)
    quality = quality_match.group("quality") if quality_match else "Unknown"
    quality = re.sub(r"\s+", "", quality).replace("WEBDL", "WEB-DL") if quality != "Unknown" else quality

    # Prefer title before the season/episode marker. Otherwise strip detected
    # episode/quality tokens so a file's title is not duplicated in a template.
    title_end = match.start() if match else None
    if title_end is not None:
        title = normalized[:title_end]
    else:
        title = normalized
        if quality_match:
            title = title[:quality_match.start()] + " " + title[quality_match.end():]
        title = _EPISODE_ONLY.sub(" ", title)
        title = re.sub(r"(?i)\bS\d{1,2}\b", " ", title)

    title = _SPACE.sub(" ", title).strip(" -._[](){}")
    return {
        "title": title or "Unknown Title",
        "season": season.zfill(2),
        "episode": str(episode).zfill(2) if episode else "01",
        "quality": quality,
    }


def sanitize_filename(filename: str, *, max_length: int = 180) -> str:
    """Return a portable basename with no path traversal or control characters."""
    value = unicodedata.normalize("NFKC", str(filename or ""))
    value = _INVALID.sub("_", value)
    value = _SPACE.sub(" ", value).strip(" .")
    value = value.replace("..", "_")
    if not value or value in {".", ".."}:
        value = "renamed_file"
    if len(value) > max_length:
        stem, ext = os.path.splitext(value)
        keep = max(1, max_length - len(ext))
        value = stem[:keep].rstrip(" .") + ext[: max_length - keep]
    return value


def render_template(template: str, filename: str) -> str:
    """Replace modern and legacy placeholders, then sanitize the result."""
    parts = parse_filename(filename)
    values = {
        "{title}": parts["title"],
        "{season}": parts["season"],
        "{episode}": parts["episode"],
        "{quality}": parts["quality"],
        "[title]": parts["title"],
        "[season]": parts["season"],
        "[episode]": "EP" + parts["episode"],
        "[quality]": parts["quality"],
    }
    rendered = str(template or "")
    for marker, value in values.items():
        rendered = rendered.replace(marker, value)
    return sanitize_filename(rendered)
