@echo off
rem Use the folder that contains this file.
cd /d "%~dp0"
rem Select the available Python command on Windows.
where py >nul 2>nul
if errorlevel 1 (
  set "RUNPY=python"
) else (
  set "RUNPY=py"
)
rem Install the two libraries, then start the site.
%RUNPY% -m pip install -r requirements.txt
if errorlevel 1 goto error
echo.
echo Keep this window open. In your browser, open http://127.0.0.1:8000
echo.
%RUNPY% app.py
echo.
pause
exit /b
:error
echo Python or the internet connection is missing. Send a picture of this window.
pause
