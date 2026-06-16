from __future__ import annotations

import argparse
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.services.license_id_generator import generate_license_ids


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Generate Meeting Cost Timer license IDs."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of license IDs to generate.",
    )
    parser.add_argument(
        "--issue-yyyymm",
        help="Issue year and month in YYYYMM format. Defaults to current month.",
    )
    args = parser.parse_args()

    for license_id in generate_license_ids(args.count, args.issue_yyyymm):
        print(license_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
