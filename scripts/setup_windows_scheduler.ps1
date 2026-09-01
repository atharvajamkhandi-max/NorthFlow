# Windows Task Scheduler Setup for NSE Money Flow Screener (17:00, 18:00, 19:00, 20:00 IST)
$PythonExe = (Get-Command python).Source
$PythonDir = Split-Path $PythonExe
$PythonwExe = Join-Path $PythonDir "pythonw.exe"
$ExecBinary = if (Test-Path $PythonwExe) { $PythonwExe } else { $PythonExe }

$ProjectDir = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ScriptPath = Join-Path $ProjectDir "scripts\daily_update.py"

Write-Host "Configuring Windows Task Scheduler..." -ForegroundColor Cyan
Write-Host "Executable:        $ExecBinary"
Write-Host "Project Directory: $ProjectDir"
Write-Host "Script:            $ScriptPath"

$Action = New-ScheduledTaskAction -Execute $ExecBinary -Argument "`"$ScriptPath`"" -WorkingDirectory $ProjectDir


$Trigger1 = New-ScheduledTaskTrigger -Daily -At "17:00"
$Trigger2 = New-ScheduledTaskTrigger -Daily -At "18:00"
$Trigger3 = New-ScheduledTaskTrigger -Daily -At "19:00"
$Trigger4 = New-ScheduledTaskTrigger -Daily -At "20:00"

$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName "NSE_Money_Flow_Daily_Update" -Action $Action -Trigger @($Trigger1, $Trigger2, $Trigger3, $Trigger4) -Settings $Settings -Force

Write-Host "`nWindows Task 'NSE_Money_Flow_Daily_Update' successfully registered!" -ForegroundColor Green
