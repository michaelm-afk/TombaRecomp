@echo off
setlocal
set "EU2_ROOT=%~dp0.."
cd /d "%EU2_ROOT%\build-eu2\native"
if not exist "Tombi__SCES_01331_Prototype.exe" (
  echo Testbuild fehlt. Siehe eu2\README.md.
  pause
  exit /b 1
)
Tombi__SCES_01331_Prototype.exe --game "%EU2_ROOT%\eu2\game.toml" --disc "%EU2_ROOT%\disc\eu2\disc.cue" --memcard-dir "%EU2_ROOT%\build-eu2\manual-cards" --no-launcher
if errorlevel 1 pause
endlocal
