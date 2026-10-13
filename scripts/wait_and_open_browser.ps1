# AI Business Architect - Bounded Readiness Poller & Browser Launcher
# Invoked as a non-blocking background helper from start_local.bat.
# Polls the application's real /ready endpoint until the server is ready,
# then opens the user's default browser at http://127.0.0.1:8000.

param(
    [string]$HealthUrl = "http://127.0.0.1:8000/ready",
    [string]$BrowserUrl = "http://127.0.0.1:8000",
    [int]$TimeoutSeconds = 30
)

$deadline = (Get-Date).AddSeconds($TimeoutSeconds)
$isReady = $false

while ((Get-Date) -lt $deadline) {
    try {
        $response = Invoke-WebRequest -Uri $HealthUrl -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $isReady = $true
            break
        }
    } catch {
        # Server still warming up or database initializing; retry
    }
    Start-Sleep -Milliseconds 800
}

if ($isReady) {
    Write-Host "`n[INFO] Application is ready! Opening $BrowserUrl in default browser..." -ForegroundColor Green
    try {
        Start-Process $BrowserUrl
    } catch {
        Write-Host "[NOTICE] Could not automatically open default browser: $_" -ForegroundColor Yellow
        Write-Host "[NOTICE] Please navigate manually to: $BrowserUrl" -ForegroundColor Cyan
    }
    exit 0
} else {
    Write-Host "`n[WARNING] Readiness probe ($HealthUrl) did not respond within $TimeoutSeconds seconds." -ForegroundColor Yellow
    Write-Host "[WARNING] Please check server logs above for errors or diagnostic details." -ForegroundColor Yellow
    exit 1
}
