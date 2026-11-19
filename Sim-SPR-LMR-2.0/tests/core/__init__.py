from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
APP_ROOT = PROJECT_ROOT / "sim-spr-lmr-simulator"

sys.path.insert(0, str(APP_ROOT))
