# ============================================
# Lily Cafe POS - Auto-Update Task Scheduler Setup
# Run this as Administrator to setup automatic updates
# ============================================

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "   ERROR: Administrator rights required" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please run this script as Administrator:" -ForegroundColor Yellow
    Write-Host "1. Right-click on setup-auto-update.ps1" -ForegroundColor Yellow
    Write-Host "2. Select 'Run with PowerShell' as Administrator" -ForegroundColor Yellow
    Write-Host ""
    pause
    exit 1
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host "   Lily Cafe POS Auto-Update Setup" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Get the current directory
$installPath = (Get-Location).Path
Write-Host "Installation path: $installPath" -ForegroundColor Green
Write-Host ""

# Verify auto-update.bat exists
if (-not (Test-Path "$installPath\auto-update.bat")) {
    Write-Host "ERROR: auto-update.bat not found!" -ForegroundColor Red
    Write-Host "Please run this script from the lily-cafe-pos directory." -ForegroundColor Red
    pause
    exit 1
}

# Ask for update time
Write-Host "When should updates run automatically?" -ForegroundColor Yellow
Write-Host "Recommended: After closing time (e.g., 3:00 AM)" -ForegroundColor Gray
Write-Host ""
$updateTime = Read-Host "Enter time in 24-hour format (e.g., 03:00)"

# Validate time format
if ($updateTime -notmatch '^\d{1,2}:\d{2}$') {
    Write-Host "Invalid time format. Using default: 03:00" -ForegroundColor Yellow
    $updateTime = "03:00"
}

Write-Host ""
Write-Host "Setting up automatic updates to run at $updateTime daily..." -ForegroundColor Cyan
Write-Host ""

try {
    # Create the scheduled task action
    $action = New-ScheduledTaskAction `
        -Execute "$installPath\auto-update.bat" `
        -WorkingDirectory $installPath

    # Create the trigger (daily at specified time)
    $trigger = New-ScheduledTaskTrigger `
        -Daily `
        -At $updateTime

    # Create task settings
    $settings = New-ScheduledTaskSettingsSet `
        -AllowStartIfOnBatteries `
        -DontStopIfGoingOnBatteries `
        -WakeToRun `
        -RestartCount 3 `
        -RestartInterval (New-TimeSpan -Minutes 10)

    # Create principal (run as SYSTEM with highest privileges)
    $principal = New-ScheduledTaskPrincipal `
        -UserId "SYSTEM" `
        -LogonType ServiceAccount `
        -RunLevel Highest

    # Check if task already exists
    $existingTask = Get-ScheduledTask -TaskName "Lily Cafe POS Auto Update" -ErrorAction SilentlyContinue

    if ($existingTask) {
        Write-Host "Task already exists. Updating..." -ForegroundColor Yellow
        Unregister-ScheduledTask -TaskName "Lily Cafe POS Auto Update" -Confirm:$false
    }

    # Register the task
    Register-ScheduledTask `
        -TaskName "Lily Cafe POS Auto Update" `
        -Action $action `
        -Trigger $trigger `
        -Settings $settings `
        -Principal $principal `
        -Description "Automatically updates Lily Cafe POS system daily at $updateTime" | Out-Null

    Write-Host ""
    Write-Host "============================================" -ForegroundColor Green
    Write-Host "   SUCCESS! Auto-update configured" -ForegroundColor Green
    Write-Host "============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Configuration:" -ForegroundColor Cyan
    Write-Host "  - Updates check: Daily at $updateTime" -ForegroundColor White
    Write-Host "  - Wake computer: Yes" -ForegroundColor White
    Write-Host "  - Run on battery: Yes" -ForegroundColor White
    Write-Host "  - Auto retry: Yes (3 attempts)" -ForegroundColor White
    Write-Host ""
    Write-Host "What happens next:" -ForegroundColor Yellow
    Write-Host "  1. Computer will wake at $updateTime daily" -ForegroundColor White
    Write-Host "  2. Check for updates from developer" -ForegroundColor White
    Write-Host "  3. Install updates if available" -ForegroundColor White
    Write-Host "  4. Log results to logs folder" -ForegroundColor White
    Write-Host "  5. Go back to sleep" -ForegroundColor White
    Write-Host ""
    Write-Host "You can also:" -ForegroundColor Cyan
    Write-Host "  - Run updates manually: Double-click update-now.bat" -ForegroundColor White
    Write-Host "  - View logs: Double-click view-update-logs.bat" -ForegroundColor White
    Write-Host "  - Check Task Scheduler: taskschd.msc" -ForegroundColor White
    Write-Host ""

    # Test if we can run the task
    Write-Host "Testing update script..." -ForegroundColor Cyan
    $testResult = & "$installPath\auto-update.bat"

    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Test successful!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Check the logs folder for test results." -ForegroundColor Gray
    } else {
        Write-Host "✗ Test had some issues. Check logs for details." -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "Setup complete! Keep your laptop plugged in at night." -ForegroundColor Green
    Write-Host ""

} catch {
    Write-Host ""
    Write-Host "============================================" -ForegroundColor Red
    Write-Host "   ERROR: Setup failed" -ForegroundColor Red
    Write-Host "============================================" -ForegroundColor Red
    Write-Host ""
    Write-Host "Error details:" -ForegroundColor Yellow
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Please try:" -ForegroundColor Yellow
    Write-Host "  1. Run as Administrator" -ForegroundColor White
    Write-Host "  2. Check Windows Task Scheduler is running" -ForegroundColor White
    Write-Host "  3. Contact your developer if issue persists" -ForegroundColor White
    Write-Host ""
    pause
    exit 1
}

pause
