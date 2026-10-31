#!/usr/bin/env python3
"""Build the Excel interview database from the survey response set.

Usage:
    python scripts/build_interview_database.py [output.xlsx]
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from interview_database.personas import SURVEY_FILE, load  # noqa: E402
from interview_database.workbook import build  # noqa: E402

DEFAULT_OUT = ROOT / "MUBAS_Mobile_Bundle_Interview_Database.xlsx"


def main() -> None:
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    people = load(ROOT / SURVEY_FILE)
    print(f"Loaded {len(people)} respondents from {SURVEY_FILE}")
    path = build(people, out)
    print(f"Wrote {path} ({path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
