"""No-crash coverage for every WMO code the renderer handles."""

import pytest
from PIL import Image, ImageDraw

from dashboard.weather_icons import _HEAVY_RAIN, draw

WMO_CODES = [
    0, 1, 2, 3,
    45, 48,
    51, 53, 55, 56, 57,
    61, 63, 65, 66, 67,
    71, 73, 75, 77,
    80, 81, 82,
    85, 86,
    95, 96, 99,
    999,  # unknown — should fall through to the cloud fallback
]


@pytest.mark.parametrize("code", WMO_CODES)
@pytest.mark.parametrize("is_day", [True, False])
def test_draw_does_not_crash(code, is_day):
    img = Image.new("1", (24, 24), 255)
    d = ImageDraw.Draw(img)
    draw(d, 2, 2, code, is_day, size=20)


def test_code_82_is_heavy():
    """Regression: code 82 (violent rain showers) used to render as light."""
    assert 82 in _HEAVY_RAIN
