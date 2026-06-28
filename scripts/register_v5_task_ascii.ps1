$ErrorActionPreference = "Stop"

$TaskName = "AI Career OS v5"
$OldTaskName = "AI Career OS v3"
$Root = "D:\ai-career-os"
$StartIn = "D:\ai-career-os\scripts"
$Python = "C:\Users\1126125669\AppData\Local\Programs\Python\Python313\python.exe"
$Script = "D:\ai-career-os\scripts\run_v5.py"
$ResultPath = "D:\ai-career-os\logs\v5_task_register_result.json"

New-Item -ItemType Directory -Force -Path (Split-Path $ResultPath) | Out-Null

$deletedOld = $false
$deletedExisting = $false

$old = Get-ScheduledTask -TaskName $OldTaskName -ErrorAction SilentlyContinue
if ($old) {
    Unregister-ScheduledTask -TaskName $OldTaskName -Confirm:$false
    $deletedOld = $true
}

$existing = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($existing) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    $deletedExisting = $true
}

$action = New-ScheduledTaskAction -Execute $Python -Argument $Script -WorkingDirectory $StartIn
$dailyTrigger = New-ScheduledTaskTrigger -Daily -At "20:30"
$logonTrigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType S4U -RunLevel Highest
$task = New-ScheduledTask -Action $action -Trigger @($dailyTrigger, $logonTrigger) -Settings $settings -Principal $principal
Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null

$registered = Get-ScheduledTask -TaskName $TaskName
$info = Get-ScheduledTaskInfo -TaskName $TaskName

$summary = [ordered]@{
    task_name = $TaskName
    old_v3_deleted = $deletedOld
    existing_v5_deleted = $deletedExisting
    created = $true
    execute = $Python
    arguments = $Script
    start_in = $StartIn
    run_level = $registered.Principal.RunLevel.ToString()
    logon_type = $registered.Principal.LogonType.ToString()
    triggers = @($registered.Triggers | ForEach-Object { $_.ToString() })
    last_task_result = $info.LastTaskResult
    next_run_time = $info.NextRunTime
}

$summary | ConvertTo-Json -Depth 5 | Set-Content -Path $ResultPath -Encoding UTF8
$summary | ConvertTo-Json -Depth 5
