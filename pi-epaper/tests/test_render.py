"""Tests for the renderer's pure helpers and overall output shape."""

from datetime import datetime

import pytest
from PIL import Image, ImageDraw

from dashboard import client, fonts, render
from dashboard.constants import DISPLAY_HEIGHT, DISPLAY_WIDTH
from dashboard.render import Frame, _format_departures, _truncate_to_width


def _snapshot(lines=None) -> client.Snapshot:
    return client.Snapshot(
        lines=lines or (client.Line("T6", "Centre", "Châtillon", (1, 11)),),
        velib=client.Velib("Foo", 0, 0),
        weather=client.Weather(20.0, 2, 5.0, 0.0, True),
        disruptions=(),
        generated_at=datetime.now(),
    )


def test_render_returns_frame_at_panel_size():
    frame = render.render(_snapshot())
    assert isinstance(frame, Frame)
    assert frame.black.size == (DISPLAY_WIDTH, DISPLAY_HEIGHT)
    assert frame.red is None


def test_render_is_pure_with_fixed_clock():
    now = datetime(2026, 1, 1, 12, 0, 0)
    a = render.render(_snapshot(), now=now)
    b = render.render(_snapshot(), now=now)
    assert a.black.tobytes() == b.black.tobytes()


def test_render_stale_indicator_changes_pixels():
    now = datetime(2026, 1, 1, 12, 0, 0)
    fresh = render.render(_snapshot(), now=now)
    stale = render.render(_snapshot(), now=now, stale=True)
    assert fresh.black.tobytes() != stale.black.tobytes()


@pytest.mark.parametrize("minutes,expected", [
    ((), "—"),
    ((5,), "5'"),
    ((1, 11), "1'  11'"),
    ((1, 11, 22), "1'  11'"),  # capped at the first two
])
def test_format_departures(minutes, expected):
    assert _format_departures(minutes) == expected


def test_truncate_short_text_unchanged():
    img = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), 255)
    d = ImageDraw.Draw(img)
    assert _truncate_to_width(d, "X", fonts.regular(12), 1000) == "X"


def test_truncate_long_text_uses_ellipsis():
    img = Image.new("1", (DISPLAY_WIDTH, DISPLAY_HEIGHT), 255)
    d = ImageDraw.Draw(img)
    out = _truncate_to_width(d, "Châtillon-Montrouge-Bagneux", fonts.regular(12), 40)
    assert out.endswith("…")
    assert len(out) < len("Châtillon-Montrouge-Bagneux")
