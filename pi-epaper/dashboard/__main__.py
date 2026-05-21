"""CLI entrypoint.

Usage:
    python -m dashboard preview [--output preview.png] [--offline]
    python -m dashboard run [--interval 60] [--once]
"""

from __future__ import annotations

import argparse
import logging
import signal
import sys
import threading
from datetime import datetime
from pathlib import Path

from . import client, render

log = logging.getLogger("dashboard")

# How long since the last successful API fetch before we flag the data as stale.
_STALE_AFTER_SECONDS = 300


def _load_snapshot(offline: bool) -> client.Snapshot:
    if offline:
        return _sample_snapshot()
    return client.fetch()


def cmd_preview(args: argparse.Namespace) -> int:
    snapshot = _load_snapshot(args.offline)
    frame = render.render(snapshot)
    output = Path(args.output)
    frame.black.save(output)
    print(f"Wrote {output} ({frame.black.size[0]}x{frame.black.size[1]})")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    from . import display  # lazy: requires waveshare-epd, Pi-only

    panel = display.Display()
    stop = _install_signal_handlers()
    last_frame: render.Frame | None = None
    last_success: datetime | None = None

    try:
        while True:
            stale = (
                last_success is None
                or (datetime.now() - last_success).total_seconds() > _STALE_AFTER_SECONDS
            )
            try:
                snapshot = client.fetch()
                last_success = datetime.now()
                stale = False
            except Exception:
                log.exception("Fetch failed")
                snapshot = None  # type: ignore[assignment]

            if snapshot is not None:
                frame = render.render(snapshot, stale=stale)
                if last_frame is None or _frame_changed(frame, last_frame):
                    panel.show(frame)
                    last_frame = frame
                    log.info("Refreshed display (stale=%s)", stale)
                else:
                    log.info("No change, skipping refresh")

            if args.once or stop.wait(timeout=args.interval):
                break
    finally:
        panel.close()
    return 0


def _frame_changed(a: render.Frame, b: render.Frame) -> bool:
    if a.black.tobytes() != b.black.tobytes():
        return True
    a_red = a.red.tobytes() if a.red is not None else None
    b_red = b.red.tobytes() if b.red is not None else None
    return a_red != b_red


def _install_signal_handlers() -> threading.Event:
    stop = threading.Event()

    def handler(signum: int, _frame: object) -> None:
        log.info("Received signal %s, shutting down", signum)
        stop.set()

    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)
    return stop


def _sample_snapshot() -> client.Snapshot:
    return client.Snapshot(
        lines=(
            client.Line("T6", "Centre de Châtillon", "Châtillon-Montrouge", (1, 11)),
            client.Line("394", "Centre de Châtillon", "Issy Val de Seine", (4, 21)),
            client.Line("388", "Mairie de Châtillon", "Porte d'Orléans", (27, 39)),
            client.Line("388", "Mairie de Châtillon", "Bourg-la-Reine", (26, 41)),
        ),
        velib=client.Velib("Henri Barbusse / Gabriel Péri", 0, 0),
        weather=client.Weather(21.2, 2, 5.1, 0.0, True),
        disruptions=(),
        generated_at=datetime.now(),
    )


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )

    parser = argparse.ArgumentParser(prog="dashboard")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_preview = sub.add_parser("preview", help="Render to PNG (no hardware)")
    p_preview.add_argument("--output", "-o", default="preview.png")
    p_preview.add_argument("--offline", action="store_true", help="Use sample data, skip API call")
    p_preview.set_defaults(func=cmd_preview)

    p_run = sub.add_parser("run", help="Refresh the ePaper periodically (Pi-only)")
    p_run.add_argument("--interval", type=float, default=60.0)
    p_run.add_argument("--once", action="store_true", help="Run a single refresh and exit")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
