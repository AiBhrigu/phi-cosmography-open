#!/usr/bin/env python3
"""Fresh completed-UTC BTC daily utility pilot entrypoint."""
from __future__ import annotations
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from tools.market_cosmographer_btc_daily_pilot.common import *
from tools.market_cosmographer_btc_daily_pilot.source import *
from tools.market_cosmographer_btc_daily_pilot.compute import *
from tools.market_cosmographer_btc_daily_pilot.packet_builder import *
from tools.market_cosmographer_btc_daily_pilot.render import *
from tools.market_cosmographer_btc_daily_pilot.utility import *
from tools.market_cosmographer_btc_daily_pilot.cli import main
if __name__ == '__main__':
    raise SystemExit(main())
