# Nexus Agents — one-command launcher (Windows PowerShell)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot\backend

if (-not (Test-Path .venv)) {
    Write-Host "Creating virtualenv..." -ForegroundColor Cyan
    py -m venv .venv
}

& .\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
$env:NO_PROXY = "*"   # avoid WinINET SOCKS proxy breaking pip downloads on this box
& .\.venv\Scripts\python.exe -m pip install --quiet -r requirements.txt

if (-not (Test-Path .env)) { Copy-Item .env.example .env }

Write-Host "`nNexus Agents → http://localhost:8000  (кабинет: /app.html)" -ForegroundColor Green
& .\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
