"""Generate the world and pin it in config/heldout.lock. Run once, before any agent code exists."""

from __future__ import annotations

import json
import shutil
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fat import lock, settings  # noqa: E402
from fat.world.generate import build  # noqa: E402

if __name__ == "__main__":
    t0 = time.time()
    for sub in ("lists", "media", "tenants", "truth"):
        shutil.rmtree(settings.DATA / sub, ignore_errors=True)
    stats = build(settings.world(), settings.DATA)
    (settings.CONFIG / "heldout.lock").write_text(json.dumps(lock.current(), indent=1) + "\n")
    print(json.dumps(stats, indent=1), f"{time.time() - t0:.1f}s")
