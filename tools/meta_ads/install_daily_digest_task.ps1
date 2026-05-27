# Register the DuberyDailyDigest scheduled task.
# Run once from PowerShell:
#   PS> .\install_daily_digest_task.ps1
#
# Idempotent -- safe to re-run (replaces existing task with same name).
# Runs as the current user, no admin required.

$TaskName = "DuberyDailyDigest"
$ScriptPath = "C:\Users\RAS\projects\DuberyMNL\tools\meta_ads\daily_digest.py"
$WorkingDir = "C:\Users\RAS\projects\DuberyMNL"
$PythonW = (Get-Command pythonw.exe -ErrorAction SilentlyContinue).Source
if (-not $PythonW) { $PythonW = "pythonw.exe" }  # fall back to PATH lookup

# Action: run pythonw (no console flash) against the digest script
$Action = New-ScheduledTaskAction -Execute $PythonW `
    -Argument "`"$ScriptPath`"" `
    -WorkingDirectory $WorkingDir

# Trigger: daily at 9:00 AM (system local time = PHT on this laptop)
$Trigger = New-ScheduledTaskTrigger -Daily -At 9:00am

# Settings:
#  - StartWhenAvailable: if laptop was asleep at 9 AM, run when it wakes
#  - ExecutionTimeLimit 5 min: catch runaway Meta API loops
#  - DontAllowDemandStart=false: lets you right-click Run manually
$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -ExecutionTimeLimit (New-TimeSpan -Minutes 5) `
    -RestartCount 1 -RestartInterval (New-TimeSpan -Minutes 10)

# Principal: current user, no admin required
$Principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive

# Drop any existing task with this name (idempotent)
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

Register-ScheduledTask -TaskName $TaskName `
    -Action $Action -Trigger $Trigger -Settings $Settings -Principal $Principal `
    -Description "Daily 9 AM PHT digest of Dubery ad performance, sent to RA's TG DM"

Write-Host ""
Write-Host "Registered scheduled task: $TaskName"
Write-Host "  Schedule: daily at 9:00 AM (local time)"
Write-Host "  Action:   $PythonW `"$ScriptPath`""
Write-Host ""
Write-Host "Verify:    Get-ScheduledTask -TaskName $TaskName | Get-ScheduledTaskInfo"
Write-Host "Run now:   Start-ScheduledTask -TaskName $TaskName"
Write-Host "Remove:    Unregister-ScheduledTask -TaskName $TaskName -Confirm:`$false"
