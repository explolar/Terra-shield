@echo off
REM TerraShield AI - CLEAN frontend dev restart (Windows cmd).
REM Fixes a corrupted dev server (blank map / white screen / vendor-chunks error)
REM by clearing the stale .next cache and starting a fresh dev server.
REM
REM 1) Close any terminal currently running "npm run dev" (Ctrl+C), then
REM 2) double-click this file (or run it from cmd).

cd /d "%~dp0..\frontend"

echo Clearing .next cache...
if exist ".next" rmdir /s /q ".next"

echo Starting a fresh dev server...
echo   Frontend -^> http://localhost:3000
npm run dev
