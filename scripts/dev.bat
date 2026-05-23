@echo off
REM TerraShield AI - one-click local dev launcher (Windows cmd).
REM Starts the FastAPI backend and the Next.js frontend in two new windows.
REM Uses "python -m uvicorn" so it works even if the Scripts dir isn't on PATH.

start "TerraShield Backend" cmd /k "cd /d %~dp0..\backend && python -m uvicorn app.main:app --reload --port 8000"
start "TerraShield Frontend" cmd /k "cd /d %~dp0..\frontend && npm run dev"

echo.
echo   TerraShield AI starting...
echo   Backend  -^> http://localhost:8000/docs
echo   Frontend -^> http://localhost:3000
echo.
