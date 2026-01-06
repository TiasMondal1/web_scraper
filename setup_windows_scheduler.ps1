# PowerShell script to set up Windows Task Scheduler for price tracker
# Run this script as Administrator

$scriptPath = (Get-Location).Path
$pythonPath = (Get-Command python).Source
$scriptFile = Join-Path $scriptPath "scheduler.py"

# Check if script exists
if (-not (Test-Path $scriptFile)) {
    Write-Host "Error: scheduler.py not found at $scriptFile" -ForegroundColor Red
    exit 1
}

# Task name
$taskName = "PriceTracker_ScheduledRun"

# Remove existing task if it exists
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    Write-Host "Removed existing task: $taskName" -ForegroundColor Yellow
}

# Create action (run Python script)
$action = New-ScheduledTaskAction -Execute $pythonPath -Argument "`"$scriptFile`" --once" -WorkingDirectory $scriptPath

# Create trigger (daily at 9 AM)
$trigger = New-ScheduledTaskTrigger -Daily -At "9:00 AM"

# Create settings
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

# Create principal (run whether user is logged in or not)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Register the task
Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Automated price tracking for web scraper"

Write-Host "Windows Task Scheduler configured successfully!" -ForegroundColor Green
Write-Host "Task Name: $taskName" -ForegroundColor Green
Write-Host "Schedule: Daily at 9:00 AM" -ForegroundColor Green
Write-Host ""
Write-Host "To modify the schedule, use Task Scheduler GUI or run:" -ForegroundColor Yellow
Write-Host "  Get-ScheduledTask -TaskName $taskName | Get-ScheduledTaskInfo" -ForegroundColor Yellow




