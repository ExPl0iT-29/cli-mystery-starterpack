from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from cli_mystery_starter.cli import main


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
