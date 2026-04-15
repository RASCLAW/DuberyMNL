Start-ScheduledTask -TaskName 'DuberyMNL-Chatbot'
Start-ScheduledTask -TaskName 'DuberyMNL-Tunnel'
Start-Sleep 6

Write-Host "--- Task states ---"
Get-ScheduledTask -TaskName 'DuberyMNL-*' | ForEach-Object {
    $info = $_ | Get-ScheduledTaskInfo
    $line = '{0,-20} State={1,-10} LastRun={2} Result=0x{3:X}' -f $_.TaskName, $_.State, $info.LastRunTime, $info.LastTaskResult
    Write-Host $line
}

Write-Host ""
Write-Host "--- Running processes ---"
Get-Process python, cloudflared -ErrorAction SilentlyContinue | ForEach-Object {
    '{0,-15} PID={1} StartTime={2}' -f $_.ProcessName, $_.Id, $_.StartTime
} | Write-Host
