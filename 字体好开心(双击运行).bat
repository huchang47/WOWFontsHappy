@echo off
title WoWFontsHappy

:: Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [Error] Node.js not found!
    echo Please install Node.js from https://nodejs.org/
    pause
    exit /b 1
)

:: Install dependencies if needed
if not exist "node_modules" (
    echo Installing dependencies...
    call npm install
)

:: Start server
echo Starting WoWFontsHappy...
node server.js

pause
