"""Render a Snapshot to a 296x128 1-bit PIL image for the Waveshare 2.9" ePaper."""

from __future__ import annotations

from datetime import datetime
from typing import NamedTuple

from PIL import Image, ImageDraw, ImageFont

from . import fonts, weather_icons
from .client import Line, Snapshot
from .constants import DISPLAY_HEIGHT, DISPLAY_WIDTH


class Frame(NamedTuple):
    """One refresh's pixel data. `red` stays None on monochrome panels;
    on the 3-color (B) variant it carries the red plane."""

    black: Image.Image
    red: Image.Image | None = None


BLACK = 0
WHITE = 255

TOP_BAR_H = 24
ROW_H = (DISPLAY_HEIGHT - TOP_BAR_H) // 4  # 26

# Font sizes used across the layout. Approximate cap-heights are used for
# vertical centering since PIL's textbbox is glyph-dependent.
TEMP_FONT_PX = 16
CLOCK_FONT_PX = 18
META_FONT_PX = 12
BADGE_FONT_PX = 14
DEPARTURE_FONT_PX = 16
DIRECTION_FONT_PX = 12


def render(snapshot: Snapshot, *, now: datetime | None = None, stale: bool = False) -> Frame:
    img = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), WHITE)
    d = ImageDraw.Draw(img)

    _draw_top_bar(d, snapshot, now or datetime.now(), stale=stale)
    d.line((0, TOP_BAR_H, DISPLAY_WIDTH, TOP_BAR_H), fill=BLACK, width=1)

    for i, line in enumerate(snapshot.lines[:4]):
        _draw_line_row(d, i, line)

    return Frame(black=img)


def _draw_top_bar(
    d: ImageDraw.ImageDraw, snap: Snapshot, now: datetime, *, stale: bool
) -> None:
    weather_icons.draw(d, 2, 2, snap.weather.weather_code, snap.weather.is_day, size=20)

    temp = f"{round(snap.weather.temperature_c)}°"
    d.text((26, 2), temp, font=fonts.bold(TEMP_FONT_PX), fill=BLACK)

    velib_total = snap.velib.mechanical + snap.velib.electrical
    velib = f"V {snap.velib.mechanical}M+{snap.velib.electrical}E" if velib_total > 0 else "V —"
    d.text((75, 5), velib, font=fonts.regular(META_FONT_PX), fill=BLACK)

    if snap.weather.precipitation_mm > 0:
        d.text(
            (150, 5),
            f"{snap.weather.precipitation_mm:.1f}mm",
            font=fonts.regular(META_FONT_PX),
            fill=BLACK,
        )

    clock = now.strftime("%H:%M")
    clock_font = fonts.bold(CLOCK_FONT_PX)
    cw = _text_width(d, clock, clock_font)
    clock_x = DISPLAY_WIDTH - cw - 2
    d.text((clock_x, 1), clock, font=clock_font, fill=BLACK)

    if stale:
        # Hollow circle sitting just left of the clock — visible but not alarming.
        d.ellipse((clock_x - 12, 8, clock_x - 6, 14), outline=BLACK, width=1)


def _draw_line_row(d: ImageDraw.ImageDraw, index: int, line: Line) -> None:
    y = TOP_BAR_H + index * ROW_H

    badge_w, badge_h = 36, 20
    badge_y = y + (ROW_H - badge_h) // 2
    d.rectangle((2, badge_y, 2 + badge_w, badge_y + badge_h), fill=BLACK)
    badge_font = fonts.bold(BADGE_FONT_PX)
    tw = _text_width(d, line.line, badge_font)
    d.text(
        (2 + (badge_w - tw) // 2, badge_y + 2),
        line.line,
        font=badge_font,
        fill=WHITE,
    )

    departures = _format_departures(line.next_departures_minutes)
    dep_font = fonts.bold(DEPARTURE_FONT_PX)
    dep_w = _text_width(d, departures, dep_font)
    dep_x = DISPLAY_WIDTH - dep_w - 3
    d.text((dep_x, y + (ROW_H - DEPARTURE_FONT_PX) // 2), departures, font=dep_font, fill=BLACK)

    dir_font = fonts.regular(DIRECTION_FONT_PX)
    direction = _truncate_to_width(d, line.direction, dir_font, dep_x - 44)
    d.text((44, y + (ROW_H - DIRECTION_FONT_PX) // 2 + 1), direction, font=dir_font, fill=BLACK)


def _format_departures(minutes: tuple[int, ...]) -> str:
    if not minutes:
        return "—"
    return "  ".join(f"{m}'" for m in minutes[:2])


def _truncate_to_width(
    d: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont, max_width: int
) -> str:
    if _text_width(d, text, font) <= max_width:
        return text
    ellipsis = "…"
    for end in range(len(text) - 1, 0, -1):
        candidate = text[:end].rstrip() + ellipsis
        if _text_width(d, candidate, font) <= max_width:
            return candidate
    return ellipsis


def _text_width(d: ImageDraw.ImageDraw, text: str, font: ImageFont.ImageFont) -> int:
    left, _, right, _ = d.textbbox((0, 0), text, font=font)
    return right - left
