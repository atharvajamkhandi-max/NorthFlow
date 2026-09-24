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

    # Export outputs to GitHub Actions if running inside workflow
    import os
    gh_output = os.environ.get("GITHUB_OUTPUT")
    new_data = (result.get("status") == "SUCCESS" and result.get("records_processed", 0) > 0)
    if gh_output:
        try:
            with open(gh_output, "a") as f:
                f.write(f"NEW_DATA={'true' if new_data else 'false'}\n")
                f.write(f"TRADE_DATE={result.get('trade_date', '')}\n")
                f.write(f"PIPELINE_STATUS={result.get('status', '')}\n")
        except Exception as e:
            logger.warning(f"Could not write to GITHUB_OUTPUT: {e}")

    if result.get("status") == "SUCCESS" and new_data:
        # Vacuum database to keep file compact
        try:
            with db.get_connection() as conn:
                conn.execute("VACUUM;")
            logger.info("Database vacuum completed successfully.")
        except Exception as e:
            logger.warning(f"Database vacuum warning: {e}")

        # If run locally with git available, automatically commit and push
        import subprocess, shutil
        git_cmd = shutil.which("git") or r"C:\Users\athar\AppData\Local\Programs\Git\cmd\git.exe"
        if Path(git_cmd).exists() or shutil.which("git"):
            try:
                base_dir = Path(__file__).resolve().parent.parent
                trade_d = result.get('trade_date', 'today')
                logger.info(f"Auto-syncing updated database ({trade_d}) to GitHub...")
                subprocess.run([git_cmd, "add", "data/market_flow.db"], cwd=str(base_dir), check=False)
                subprocess.run([git_cmd, "commit", "-m", f"chore(data): automated bhavcopy daily update for {trade_d} [skip ci]"], cwd=str(base_dir), check=False)
                push_res = subprocess.run([git_cmd, "push", "origin", "main"], cwd=str(base_dir), capture_output=True, text=True)
                if push_res.returncode == 0:
                    logger.info("Successfully pushed updated market data to GitHub!")
                else:
                    logger.info(f"Git push note: {push_res.stderr.strip() or push_res.stdout.strip()}")
            except Exception as e:
                logger.warning(f"Git auto-sync skipped / encountered: {e}")

    if result.get("status") == "FAILED":
        sys.exit(1)


if __name__ == "__main__":
    main()

