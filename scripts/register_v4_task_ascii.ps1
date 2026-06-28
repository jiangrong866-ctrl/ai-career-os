$ErrorActionPreference = "Stop"

$taskName = "AI Career OS v3"
$pythonExe = "C:\Users\1126125669\AppData\Local\Programs\Python\Python313\python.exe"
$script = "D:\ai-career-os\scripts\run_v4.py"
$workdir = "D:\ai-career-os\scripts"
$resultPath = "D:\ai-career-os\logs\v4_task_register_result.json"

New-Item -ItemType Directory -Force -Path (Split-Path $resultPath) | Out-Null

$result = [ordered]@{
  task_name = $taskName
  user = "$env:USERDOMAIN\$env:USERNAME"
  is_admin = $false
  deleted_old_task = $false
  created = $false
  run_level_highest = $false
  logon_type = $null
  daily_trigger = $false
  logon_trigger = $false
  action_program = $pythonExe
  action_arguments = "`"$script`""
  start_in = $workdir
  error = $null
}

try {
  $principalCheck = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
  $result.is_admin = $principalCheck.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
  $existing = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
  if ($existing) {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
    $result.deleted_old_task = $true
  }
  $action = New-ScheduledTaskAction -Execute $pythonExe -Argument "`"$script`"" -WorkingDirectory $workdir
  $triggerDaily = New-ScheduledTaskTrigger -Daily -At "20:30"
  $triggerLogon = New-ScheduledTaskTrigger -AtLogOn -User "$env:USERDOMAIN\$env:USERNAME"
  $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit (New-TimeSpan -Minutes 45) -MultipleInstances IgnoreNew
  $principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" -LogonType S4U -RunLevel Highest
  Register-ScheduledTask -TaskName $taskName -Action $action -Trigger @($triggerDaily, $triggerLogon) -Settings $settings -Principal $principal -Description "AI Career OS v4 monitored daily run" -Force | Out-Null
  $task = Get-ScheduledTask -TaskName $taskName
  $result.created = $true
  $result.run_level_highest = ($task.Principal.RunLevel -eq "Highest")
  $result.logon_type = [string]$task.Principal.LogonType
  $result.daily_trigger = ($task.Triggers | Where-Object { $_.StartBoundary -like "*20:30*" }).Count -gt 0
  $result.logon_trigger = ($task.Triggers | Where-Object { $_.UserId -like "$env:USERDOMAIN\$env:USERNAME" }).Count -gt 0
} catch {
  $result.error = $_.Exception.Message
}

$result | ConvertTo-Json -Depth 8 | Set-Content -Path $resultPath -Encoding UTF8
$result | ConvertTo-Json -Depth 8
if (-not $result.created -or -not $result.run_level_highest -or $result.logon_type -ne "S4U") {
  exit 1
}
