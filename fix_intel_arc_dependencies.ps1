# Script to fix Intel Arc GPU dependencies
# This script installs missing system dependencies for Intel Arc

Write-Host "=== Intel Arc GPU Dependencies Fix ===" -ForegroundColor Cyan

# Check Windows version
$osInfo = Get-WmiObject -Class Win32_OperatingSystem
Write-Host "Windows Version: $($osInfo.Caption) $($osInfo.Version)" -ForegroundColor Yellow

# Check if Intel GPU is detected
Write-Host "`nChecking Intel GPU..." -ForegroundColor Yellow
$intelGPU = Get-WmiObject -Class Win32_VideoController | Where-Object { 
    $_.Name -like "*Intel*Arc*" -or 
    $_.Name -like "*Intel*Graphics*" -or 
    $_.Name -like "*Intel*Iris*" 
}

if ($intelGPU) {
    Write-Host "✅ Intel GPU found: $($intelGPU.Name)" -ForegroundColor Green
    Write-Host "Driver Version: $($intelGPU.DriverVersion)" -ForegroundColor Green
} else {
    Write-Host "❌ Intel GPU not detected!" -ForegroundColor Red
    Write-Host "Please install Intel Arc drivers first:" -ForegroundColor Yellow
    Write-Host "https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-whql-windows.html" -ForegroundColor Cyan
    exit 1
}

# Check Visual C++ Redistributable
Write-Host "`nChecking Visual C++ Redistributable..." -ForegroundColor Yellow
$vcRedist = Get-WmiObject -Class Win32_Product | Where-Object { 
    $_.Name -like "*Microsoft Visual C++*Redistributable*" 
}

if ($vcRedist) {
    Write-Host "✅ Visual C++ Redistributable found" -ForegroundColor Green
} else {
    Write-Host "❌ Visual C++ Redistributable not found!" -ForegroundColor Red
    Write-Host "Installing Visual C++ Redistributable..." -ForegroundColor Yellow
    
    # Download and install VC++ Redistributable
    $vcUrl = "https://aka.ms/vs/17/release/vc_redist.x64.exe"
    $vcInstaller = "$env:TEMP\vc_redist.x64.exe"
    
    try {
        Invoke-WebRequest -Uri $vcUrl -OutFile $vcInstaller
        Start-Process -FilePath $vcInstaller -ArgumentList "/quiet", "/norestart" -Wait
        Write-Host "✅ Visual C++ Redistributable installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install Visual C++ Redistributable" -ForegroundColor Red
        Write-Host "Please install manually: https://aka.ms/vs/17/release/vc_redist.x64.exe" -ForegroundColor Yellow
    }
}

# Check Intel oneAPI runtime
Write-Host "`nChecking Intel oneAPI runtime..." -ForegroundColor Yellow
$oneAPIPath = "${env:ProgramFiles(x86)}\Intel\oneAPI"
if (Test-Path $oneAPIPath) {
    Write-Host "✅ Intel oneAPI found at: $oneAPIPath" -ForegroundColor Green
} else {
    Write-Host "❌ Intel oneAPI not found!" -ForegroundColor Red
    Write-Host "Installing Intel oneAPI Base Toolkit..." -ForegroundColor Yellow
    
    # Download Intel oneAPI Base Toolkit
    $oneAPIUrl = "https://registrationcenter-download.intel.com/akdlm/IRC_NAS/992857b9-624c-45b5-8961-73a5e2f6d6bb/oneAPI_Base_Toolkit_2024.0.0.49563_offline.exe"
    $oneAPIInstaller = "$env:TEMP\oneAPI_Base_Toolkit.exe"
    
    try {
        Write-Host "Downloading Intel oneAPI Base Toolkit (this may take a while)..." -ForegroundColor Yellow
        Invoke-WebRequest -Uri $oneAPIUrl -OutFile $oneAPIInstaller
        Write-Host "Installing Intel oneAPI Base Toolkit..." -ForegroundColor Yellow
        Start-Process -FilePath $oneAPIInstaller -ArgumentList "--silent", "--eula=accept" -Wait
        Write-Host "✅ Intel oneAPI Base Toolkit installed" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install Intel oneAPI" -ForegroundColor Red
        Write-Host "Please install manually: https://www.intel.com/content/www/us/en/developer/tools/oneapi/base-toolkit-download.html" -ForegroundColor Yellow
    }
}

# Set environment variables
Write-Host "`nSetting environment variables..." -ForegroundColor Yellow
$envVars = @{
    "INTEL_EXTENSION_FOR_PYTORCH_VERBOSE" = "1"
    "SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS" = "1"
    "XPU_DEVICE_ID" = "0"
    "ONEAPI_DEVICE_SELECTOR" = "level_zero:gpu"
}

foreach ($var in $envVars.GetEnumerator()) {
    [Environment]::SetEnvironmentVariable($var.Key, $var.Value, "User")
    Write-Host "Set $($var.Key) = $($var.Value)" -ForegroundColor Green
}

Write-Host "`n=== Dependencies Fix Complete ===" -ForegroundColor Green
Write-Host "Please restart your terminal and run:" -ForegroundColor Cyan
Write-Host "conda activate lfp_bot_intel_arc" -ForegroundColor White
Write-Host "python check_gpu.py" -ForegroundColor White 