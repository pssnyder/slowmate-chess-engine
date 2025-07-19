@echo off
REM SlowMate Chess Engine - UCI Launcher
REM This batch file starts the SlowMate engine for UCI-compatible GUIs

cd /d "%~dp0"
"%~dp0.venv\Scripts\python.exe" "%~dp0slowmate_uci.py" %*
