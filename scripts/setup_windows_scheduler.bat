@echo off
echo Configuring Windows Task Scheduler for NSE Money Flow Daily Update...
powershell -ExecutionPolicy Bypass -File "%~dp0setup_windows_scheduler.ps1"
pause
