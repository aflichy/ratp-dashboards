"""Font resolution with cross-platform fallbacks.

DejaVu Sans on Raspberry Pi OS, Arial/Helvetica on macOS as fallback.
"""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

log = logging.getLogger(__name__)

_REGULAR_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/Library/Fonts/Arial.ttf",
    "/System/Library/Fonts/Supplemental/Arial.ttf",
    "/Library/Fonts/DejaVuSans.ttf",
)

_BOLD_CANDIDATES = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/DejaVuSans-Bold.ttf",
)


def _first_existing(paths: tuple[str, ...]) -> str | None:
    for path in paths:
        if Path(path).exists():
            return path
    return None


@lru_cache(maxsize=16)
def regular(size: int) -> ImageFont.ImageFont:
    path = _first_existing(_REGULAR_CANDIDATES)
    if path is None:
        log.warning("No TTF found, falling back to PIL default bitmap font (size param ignored)")
        return ImageFont.load_default()
    return ImageFont.truetype(path, size)


@lru_cache(maxsize=16)
def bold(size: int) -> ImageFont.ImageFont:
    path = _first_existing(_BOLD_CANDIDATES)
    if path is None:
        return regular(size)
    return ImageFont.truetype(path, size)
