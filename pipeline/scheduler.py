"""
Pipeline Scheduler for Windows Task Scheduler and Local Background Daemon.
Supports execution at configured checkpoints: 17:00, 18:00, 19:00, 20:00 IST.
"""

import sys
import time
import datetime
import logging
from typing import Optional
from pathlib import Path

from config.settings import DAILY_UPDATE_TIMES, TIMEZONE
from pipeline.daily_runner import DailyPipelineRunner
from database.db import Database

logger = logging.getLogger(__name__)


def run_scheduled_checkpoint(db: Optional[Database] = None, force: bool = False):
    """
    Triggered by Windows Task Scheduler or background timer.
    Determines current checkpoint time and executes DailyPipelineRunner.
    """
    runner = DailyPipelineRunner(db=db)
    result = runner.run_checkpoint(force=force)
    return result


def generate_windows_task_command() -> str:
    """
    Generates PowerShell command to register the Windows Task Scheduler jobs.
    """
    python_exe = sys.executable
    script_path = str(Path(__file__).resolve().parent.parent / "scripts" / "daily_update.py")
    
    cmd = f"""
# Register Windows Task Scheduler for 17:00, 18:00, 19:00, 20:00 IST
$Action = New-ScheduledTaskAction -Execute "{python_exe}" -Argument '"{script_path}"'
$Triggers = @(
    New-ScheduledTaskTrigger -Daily -At "17:00",
    New-ScheduledTaskTrigger -Daily -At "18:00",
    New-ScheduledTaskTrigger -Daily -At "19:00",
    New-ScheduledTaskTrigger -Daily -At "20:00"
)
$Principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
Register-ScheduledTask -TaskName "NSE_Money_Flow_Daily_Update" -Action $Action -Trigger $Triggers -Principal $Principal -Settings $Settings -Force
"""
    return cmd
