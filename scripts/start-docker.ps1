# Start Docker Desktop and wait until the daemon is ready.
$dockerExe = "C:\Program Files\Docker\Docker\resources\bin\docker.exe"
$desktopExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"

if (-not (Test-Path $dockerExe)) {
    Write-Error "Docker is not installed. Install Docker Desktop from https://www.docker.com/products/docker-desktop/"
    exit 1
}

if (-not (Get-Process -Name "Docker Desktop" -ErrorAction SilentlyContinue)) {
    Write-Host "Starting Docker Desktop..."
    Start-Process $desktopExe
}

Write-Host "Waiting for Docker engine..."
for ($i = 1; $i -le 36; $i++) {
    & $dockerExe version *> $null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Docker is ready."
        exit 0
    }
    Start-Sleep -Seconds 5
}

Write-Error @"
Docker did not become ready within 3 minutes.

Try manually:
  1. Open 'Docker Desktop' from the Start menu
  2. Wait until the whale icon says 'Docker Desktop is running'
  3. If it stays stuck, open Docker Desktop -> Troubleshoot -> Restart
  4. Ensure WSL 2 is enabled: wsl --update
"@
exit 1