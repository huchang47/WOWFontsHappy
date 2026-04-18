@echo off
chcp 65001 >nul

echo Checking admin privileges...

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [Error] Please run this script as administrator
    echo Right-click this file and select "Run as administrator"
    pause
    exit /b 1
)

echo [OK] Admin privileges granted
echo.
echo Starting WoWFontsHappy...
echo (Running with administrator privileges)
echo.

:: Check if Node.js is installed
where node >nul 2>&1
if %errorLevel% neq 0 (
    echo [Error] Node.js not found. Please install Node.js first
    echo Download: https://nodejs.org/
    pause
    exit /b 1
)

echo [OK] Node.js is installed
echo.
echo Starting server...
echo.

:: Change to script directory
cd /d "%~dp0"

:: Start server
node server.js

if %errorLevel% neq 0 (
    echo.
    echo [Error] Server failed to start
    pause
)
