# Create a shortcut to start the bot
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Start LFP Bot.lnk")
$Shortcut.TargetPath = "powershell.exe"
$Shortcut.Arguments = "-NoExit -ExecutionPolicy Bypass -File `"$PSScriptRoot\start_bot.ps1`""
$Shortcut.WorkingDirectory = $PSScriptRoot
$Shortcut.IconLocation = "$env:USERPROFILE\.conda\envs\lfp_bot_py311\python.exe, 0"
$Shortcut.WindowStyle = 1  # 1 = Normal window, 3 = Maximized, 7 = Minimized
$Shortcut.Description = "Start LFP Telegram Bot"
$Shortcut.Save()

Write-Host "Shortcut created on Desktop: 'Start LFP Bot.lnk'" -ForegroundColor Green
