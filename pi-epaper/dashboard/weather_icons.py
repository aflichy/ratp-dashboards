"""Small weather glyphs drawn from PIL primitives.

WMO codes from open-meteo: https://open-meteo.com/en/docs#weathervariables
"""

from __future__ import annotations

import math

from PIL import ImageDraw

BLACK = 0

# Heaviest intensity within each rain/drizzle/shower category (WMO).
_HEAVY_RAIN = frozenset({55, 57, 65, 67, 82})
_RAIN_CODES = frozenset({51, 53, 55, 56, 57, 61, 63, 65, 66, 67, 80, 81, 82})


def draw(d: ImageDraw.ImageDraw, x: int, y: int, code: int, is_day: bool, size: int = 20) -> None:
    """Draw a weather icon with its top-left corner at (x, y) in a `size`x`size` box."""
    cx = x + size // 2
    cy = y + size // 2
    if code == 0:
        _sun_or_moon(d, cx, cy, size // 2 - 2, is_day)
    elif code in (1, 2):
        _partly_cloudy(d, x, y, size, is_day)
    elif code == 3:
        _cloud(d, x, y, size)
    elif code in (45, 48):
        _fog(d, x, y, size)
    elif code in _RAIN_CODES:
        _rain(d, x, y, size, heavy=code in _HEAVY_RAIN)
    elif code in (71, 73, 75, 77, 85, 86):
        _snow(d, x, y, size)
    elif code in (95, 96, 99):
        _thunder(d, x, y, size)
    else:
        _cloud(d, x, y, size)


def _sun_or_moon(d: ImageDraw.ImageDraw, cx: int, cy: int, r: int, is_day: bool) -> None:
    if is_day:
        d.ellipse((cx - r + 2, cy - r + 2, cx + r - 2, cy + r - 2), outline=BLACK, width=1)
        for i in range(8):
            a = i * math.pi / 4
            x1 = cx + int(math.cos(a) * (r - 1))
            y1 = cy + int(math.sin(a) * (r - 1))
            x2 = cx + int(math.cos(a) * (r + 2))
            y2 = cy + int(math.sin(a) * (r + 2))
            d.line((x1, y1, x2, y2), fill=BLACK, width=1)
    else:
        d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=BLACK)
        d.ellipse((cx - r + 3, cy - r, cx + r, cy + r - 3), fill=255)


def _cloud(d: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    w = size
    base_y = y + size - 4
    d.ellipse((x + 1, y + size // 3, x + size // 2, base_y), fill=BLACK)
    d.ellipse((x + size // 3, y + 2, x + size - 2, base_y - 2), fill=BLACK)
    d.ellipse((x + size // 2, y + size // 3, x + w - 1, base_y), fill=BLACK)
    d.rectangle((x + size // 4, y + size // 2, x + w - size // 4, base_y), fill=BLACK)


def _partly_cloudy(d: ImageDraw.ImageDraw, x: int, y: int, size: int, is_day: bool) -> None:
    _sun_or_moon(d, x + size // 3, y + size // 3 + 1, size // 4, is_day)
    _cloud(d, x + size // 4, y + size // 3, size * 3 // 4)


def _fog(d: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    for i, dy in enumerate((4, 9, 14)):
        d.line((x + 1 + (i % 2) * 2, y + dy, x + size - 2, y + dy), fill=BLACK, width=2)


def _rain(d: ImageDraw.ImageDraw, x: int, y: int, size: int, heavy: bool) -> None:
    _cloud(d, x, y - 2, size)
    drops = 4 if heavy else 3
    spacing = size // (drops + 1)
    for i in range(drops):
        dx = x + spacing * (i + 1)
        d.line((dx, y + size - 4, dx - 2, y + size), fill=BLACK, width=1)


def _snow(d: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    _cloud(d, x, y - 2, size)
    for i, dx_off in enumerate((4, size // 2, size - 5)):
        cx, cy = x + dx_off, y + size - 2
        d.line((cx - 2, cy, cx + 2, cy), fill=BLACK, width=1)
        d.line((cx, cy - 2, cx, cy + 2), fill=BLACK, width=1)


def _thunder(d: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    _cloud(d, x, y - 2, size)
    cx = x + size // 2
    by = y + size - 6
    d.polygon(
        (cx, by, cx + 4, by + 3, cx + 1, by + 3, cx + 3, by + 7, cx - 2, by + 2, cx + 1, by + 2),
        fill=BLACK,
    )
