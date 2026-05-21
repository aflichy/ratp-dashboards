"""Push a rendered Frame to the Waveshare 2.9" ePaper.

Only import this module on the Raspberry Pi — the waveshare-epd package
depends on RPi.GPIO/spidev which won't install on macOS.

To swap to a different 2.9" variant, change `_MODEL` below. Common options:
  - "epd2in9_V2"  — 2.9" V2 monochrome (default)
  - "epd2in9_V4"  — 2.9" V4 monochrome (faster refresh, supports partial)
  - "epd2in9b_V4" — 2.9" V4 black/white/red (needs renderer changes)
"""

from __future__ import annotations

import importlib
import logging
from typing import Any

from .constants import DISPLAY_HEIGHT, DISPLAY_WIDTH
from .render import Frame

log = logging.getLogger(__name__)

_MODEL = "epd2in9_V2"


class Display:
    def __init__(self) -> None:
        log.info("Initializing %s panel over SPI…", _MODEL)
        module = importlib.import_module(f"waveshare_epd.{_MODEL}")
        self._epd = module.EPD()
        self._epd.init()
        self._epd.Clear(0xFF)
        log.info("Panel ready")

    def show(self, frame: Frame) -> None:
        assert frame.black.size == (DISPLAY_WIDTH, DISPLAY_HEIGHT), (
            f"Renderer must produce {DISPLAY_WIDTH}x{DISPLAY_HEIGHT}, got {frame.black.size}"
        )
        portrait = frame.black.rotate(-90, expand=True)
        self._epd.display(self._epd.getbuffer(portrait))

    def close(self) -> None:
        try:
            self._epd.sleep()
        finally:
            module: Any = importlib.import_module("waveshare_epd.epdconfig")
            module.module_exit()
