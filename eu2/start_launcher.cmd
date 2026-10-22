@echo off
set "TOMBI_SOURCE=%~dp0.."
"%TOMBI_SOURCE%\build-eu2-launcher\native\overlay_toolchain\python\python.exe" -I -B "%TOMBI_SOURCE%\tools\regional\start_local.py" --region eu2 --launcher
if errorlevel 1 pause
