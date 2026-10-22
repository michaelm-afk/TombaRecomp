@echo off
set "TOMBI_SOURCE=%~dp0..\.."
"%TOMBI_SOURCE%\build-startup\comparison\eu1\overlay_toolchain\python\python.exe" -I -B "%TOMBI_SOURCE%\tools\regional\start_local.py" --region eu1
if errorlevel 1 pause
