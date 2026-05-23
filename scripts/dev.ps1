<#
  TerraShield AI — one-shot local dev launcher (Windows / PowerShell).
  Starts the FastAPI backend and the Next.js frontend in separate windows.

  Usage:  ./scripts/dev.ps1
#>
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot

Write-Host "TerraShield AI - starting backend + frontend..." -ForegroundColor Cyan

# Backend  (python -m uvicorn works even when the Scripts dir isn't on PATH)
Start-Process powershell -ArgumentList @(
  "-NoExit", "-Command",
  "cd '$root\backend'; python -m uvicorn app.main:app --reload --port 8000"
)

# Frontend
Start-Process powershell -ArgumentList @(
  "-NoExit", "-Command",
  "cd '$root\frontend'; npm run dev"
)

Write-Host "Backend  -> http://localhost:8000/docs" -ForegroundColor Green
Write-Host "Frontend -> http://localhost:3000"       -ForegroundColor Green
