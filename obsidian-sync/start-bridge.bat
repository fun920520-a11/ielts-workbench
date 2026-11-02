@echo off
chcp 65001 >nul
title IELTS Workbench - Bridge (sync + local ASR)
cd /d "%~dp0"

set "PAGE=https://www.workbuddy.cn/space/d/h9BN0kNcLlrkdqkuzvaRf5"
set "PORT=8787"

echo ============================================================
echo   IELTS Workbench - Bridge (Obsidian sync + local ASR)
echo   Source: Obsidian vault / 09 English / IELTS notes
echo ============================================================
echo.

REM ---------- 1. find a working Python ----------
REM Prefer the project venv created by podcast-bridge\install-asr.bat,
REM because that one has faster-whisper (needed for audio subtitles).
set "PY="
set "ASR=no"

set "CAND=%~dp0..\podcast-bridge\.venv\Scripts\python.exe"
if not exist "%CAND%" goto TRY_WB
"%CAND%" -c "import sys" >nul 2>nul
if errorlevel 1 goto TRY_WB
"%CAND%" -c "import faster_whisper" >nul 2>nul
if errorlevel 1 goto TRY_WB
set "PY=%CAND%"
set "ASR=yes"
goto PY_OK

:TRY_WB
set "CAND=%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%CAND%" goto TRY_PATH
"%CAND%" -c "import sys" >nul 2>nul
if errorlevel 1 goto TRY_PATH
set "PY=%CAND%"
goto PY_OK

:TRY_PATH
where py >nul 2>nul
if not errorlevel 1 (
  py -c "import sys" >nul 2>nul
  if not errorlevel 1 set "PY=py"
)
if defined PY goto PY_OK
where python >nul 2>nul
if not errorlevel 1 (
  python -c "import sys" >nul 2>nul
  if not errorlevel 1 set "PY=python"
)
if defined PY goto PY_OK
where python3 >nul 2>nul
if not errorlevel 1 (
  python3 -c "import sys" >nul 2>nul
  if not errorlevel 1 set "PY=python3"
)

:PY_OK
if not defined PY goto NOPY
echo [1/3] Python: %PY%

REM ---------- 2. 8787 已被占用：桥已经开着了，直接打开现有页面 ----------
netstat -ano | findstr /r /c:":8787 .*LISTENING" >nul 2>nul
if errorlevel 1 goto PORT_OK
echo [2/3] 8787 已有同步桥在运行 -^> 直接打开现有页面
echo       不要开第二个：两个端口 = 两套本地数据，进度会看起来像「丢了」
start "" "http://127.0.0.1:8787/"
exit /b 0
:PORT_OK
echo [2/3] Port: %PORT%
:PORT_DONE

REM ---------- 3. start the bridge ----------
set "OPENURL=http://127.0.0.1:%PORT%/"
echo [3/3] Starting... your browser will open the local workbench.
echo.
echo   Local workbench : %OPENURL%
echo   Online workbench: %PAGE%
if "%ASR%"=="yes" (
  echo   Local ASR       : READY  ^(auto subtitles for your own audio^)
) else (
  echo   Local ASR       : OFF    ^(run podcast-bridge\install-asr.bat once^)
  echo                     Playing audio and manual subtitles still work.
)
echo.
echo   KEEP THIS WINDOW OPEN while using sync or audio subtitles.
echo   Close it = bridge stops (page falls back to the built-in snapshot).
echo.

"%PY%" obsidian_sync.py serve --port %PORT% --open "%OPENURL%"

echo.
echo Bridge stopped. If it failed, please screenshot the error above.
pause
exit /b 0

:NOPY
echo [ERROR] No working Python 3 found.
echo.
echo Try one of these:
echo   1) Check this file exists:
echo      %USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe
echo   2) Run manually in PowerShell:
echo      cd "%~dp0"
echo      python obsidian_sync.py serve --port 8787 --open "%PAGE%"
echo.
echo NOTE: if double-click opens the Microsoft Store, your "python" is a
echo       Windows placeholder. Install real Python 3 (tick Add to PATH).
pause
exit /b 1
