#!/usr/bin/env bash
set -euo pipefail
P="/mnt/c/swiss_ephemerise/ephe"
echo "SWE_EPHE_PATH=$P"
[ -d "$P" ] || { echo "ERROR: MISSING_DIR"; exit 1; }
echo "FILES=$(find "$P" -maxdepth 1 -type f | wc -l | tr -d " ")"
python3 - << 'PY'
import swisseph as swe
from datetime import datetime
swe.set_ephe_path("/mnt/c/swiss_ephemerise/ephe")
dt=datetime.utcnow(); jd=swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)
lon = swe.calc_ut(jd, swe.SUN)[0][0]
print("SUN_LON", round(lon,6))
print("pyswisseph_ok", getattr(swe,"__version__","unknown"))
PY
