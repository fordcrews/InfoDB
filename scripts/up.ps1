# Start InfoDB via Docker Compose (starts Docker Desktop first if needed).
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent

& "$PSScriptRoot\start-docker.ps1"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$docker = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
Set-Location $root

if (-not (Test-Path "$root\.env")) {
    Copy-Item "$root\.env.example" "$root\.env"
    Write-Host "Created .env from .env.example — edit passwords before production use."
}

& $docker compose up --build