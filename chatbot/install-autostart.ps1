# Registers Task Scheduler entries for DuberyMNL chatbot auto-start at logon.
# Runs under current user, no admin required. Safe to re-run (uses -Force).

$root = "C:\Users\RAS\projects\DuberyMNL\chatbot"
$user = "$env:USERDOMAIN\$env:USERNAME"

function Register-HiddenLogonTask {
    param([string]$Name, [string]$Bat)
    $action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument "/c `"$Bat`""
    $trigger = New-ScheduledTaskTrigger -AtLogOn -User $user
    $principal = New-ScheduledTaskPrincipal -UserId $user -LogonType Interactive -RunLevel Limited
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable -Hidden -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $trigger -Principal $principal -Settings $settings -Force | Out-Null
    Write-Host "Registered: $Name"
}

Register-HiddenLogonTask -Name "DuberyMNL-Chatbot" -Bat "$root\start-chatbot.bat"
Register-HiddenLogonTask -Name "DuberyMNL-Tunnel"  -Bat "$root\start-tunnel.bat"

Write-Host ""
Write-Host "Registered tasks:"
Get-ScheduledTask -TaskName "DuberyMNL-*" | Select-Object TaskName, State | Format-Table -AutoSize
