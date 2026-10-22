@echo off
REM ---------------------------------------------------------------------------
REM  start_demo.bat -- opens the server and the client in two windows.
REM
REM  Usage:  double-click this file, or run:  start_demo.bat 5000
REM          (the number is the port; 5000 is used when you give none)
REM ---------------------------------------------------------------------------
setlocal
set PORT=%1
if "%PORT%"=="" set PORT=5000

cd /d "%~dp0"

echo Starting the server on port %PORT% ...
start "SOCKET SERVER - port %PORT%" cmd /k python server.py --port %PORT%

REM wait about 2 seconds without relying on stdin (timeout needs a console)
ping -n 3 127.0.0.1 >nul

echo Starting the client ...
start "SOCKET CLIENT - port %PORT%" cmd /k python client.py --port %PORT%

echo.
echo Two windows opened:
echo   1) SOCKET SERVER  - leave it running, it prints every message it gets
echo   2) SOCKET CLIENT  - type a message there and press Enter
echo.
echo Type /quit in the client window to close the connection.
echo Close the server window with Ctrl+C when you are done.
ping -n 7 127.0.0.1 >nul
endlocal
