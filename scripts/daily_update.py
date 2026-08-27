"""
Daily Automatic Update Pipeline CLI Script.
Scheduled at 17:00, 18:00, 19:00, 20:00 IST.
"""

import sys
import argparse
import logging
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pipeline.daily_runner import DailyPipelineRunner
from database.db import Database

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("daily_update")


def main():
    parser = argparse.ArgumentParser(description="Daily NSE Data Pipeline Runner")
    parser.add_argument("--date", type=str, default=None, help="Target trade date (YYYY-MM-DD)")
    parser.add_argument("--checkpoint", type=str, default=None, help="Checkpoint time (e.g. 17:00, 18:00, 19:00, 20:00)")
    parser.add_argument("--force", action="store_true", help="Force execution ignoring idempotency")
    args = parser.parse_args()

    print("=" * 60)
    print(" INDIAN STOCK MARKET INDUSTRY MONEY FLOW - DAILY PIPELINE")
    print("=" * 60)

    db = Database()
    runner = DailyPipelineRunner(db=db)
    result = runner.run_checkpoint(
        target_date=args.date,
        checkpoint_time_str=args.checkpoint,
        force=args.force
    )

    print(f"\nResult Status:  {result.get('status')}")
    print(f"Trade Date:     {result.get('trade_date')}")
    print(f"Checkpoint:     {result.get('checkpoint')} IST")
    print(f"Message:        {result.get('message')}")
    print("=" * 60 + "\n")

    if result.get("status") == "FAILED":
        sys.exit(1)


if __name__ == "__main__":
    main()
