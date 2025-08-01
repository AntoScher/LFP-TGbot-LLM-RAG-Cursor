# Diagnostic and Fix Script for Intel Arc GPU Issues
# This script analyzes the current environment and fixes common issues

Write-Host "=== Intel Arc GPU Diagnostic and Fix ===" -ForegroundColor Cyan

# Check current conda environment
Write-Host "`n1. Checking current conda environment..." -ForegroundColor Yellow
$currentEnv = conda info --envs | Select-String "\*" | ForEach-Object { ($_ -split "\s+")[0] }
Write-Host "Current environment: $currentEnv" -ForegroundColor Green

# Check if we're in the right environment
if ($currentEnv -ne "lfp_bot_intel_arc") {
    Write-Host "⚠️  Not in Intel Arc environment. Activating..." -ForegroundColor Yellow
    conda activate lfp_bot_intel_arc
}

# Check PyTorch installation
Write-Host "`n2. Checking PyTorch installation..." -ForegroundColor Yellow
try {
    $torchVersion = conda run -n lfp_bot_intel_arc python -c "import torch; print(torch.__version__)"
    Write-Host "PyTorch version: $torchVersion" -ForegroundColor Green
    
    if ($torchVersion -like "*+cpu*") {
        Write-Host "✅ PyTorch CPU version detected (correct for Intel Extension)" -ForegroundColor Green
    } else {
        Write-Host "⚠️  PyTorch version may not be compatible with Intel Extension" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ PyTorch not installed or not accessible" -ForegroundColor Red
}

# Check Intel Extension for PyTorch
Write-Host "`n3. Checking Intel Extension for PyTorch..." -ForegroundColor Yellow
try {
    $ipexVersion = conda run -n lfp_bot_intel_arc python -c "import intel_extension_for_pytorch as ipex; print(ipex.__version__)"
    Write-Host "Intel Extension for PyTorch version: $ipexVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Intel Extension for PyTorch not installed or has issues" -ForegroundColor Red
    Write-Host "Running dependency fix..." -ForegroundColor Yellow
    .\fix_intel_arc_dependencies.ps1
}

# Check XPU availability
Write-Host "`n4. Checking XPU availability..." -ForegroundColor Yellow
try {
    $xpuCheck = conda run -n lfp_bot_intel_arc python -c "import torch; print('XPU available:', hasattr(torch, 'xpu')); print('XPU is_available:', torch.xpu.is_available() if hasattr(torch, 'xpu') else 'N/A')"
    Write-Host $xpuCheck -ForegroundColor Green
    
    if ($xpuCheck -like "*XPU is_available: False*") {
        Write-Host "❌ XPU not available. This indicates missing system dependencies." -ForegroundColor Red
        Write-Host "Running dependency fix..." -ForegroundColor Yellow
        .\fix_intel_arc_dependencies.ps1
    }
} catch {
    Write-Host "❌ Error checking XPU availability" -ForegroundColor Red
}

# Check Intel GPU drivers
Write-Host "`n5. Checking Intel GPU drivers..." -ForegroundColor Yellow
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
    Write-Host "Please install Intel Arc drivers:" -ForegroundColor Yellow
    Write-Host "https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-whql-windows.html" -ForegroundColor Cyan
}

# Check environment variables
Write-Host "`n6. Checking environment variables..." -ForegroundColor Yellow
$envVars = @("INTEL_EXTENSION_FOR_PYTORCH_VERBOSE", "SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS", "XPU_DEVICE_ID", "ONEAPI_DEVICE_SELECTOR")
foreach ($var in $envVars) {
    $value = [Environment]::GetEnvironmentVariable($var, "User")
    if ($value) {
        Write-Host "✅ $var = $value" -ForegroundColor Green
    } else {
        Write-Host "❌ $var not set" -ForegroundColor Red
    }
}

# Check Intel oneAPI
Write-Host "`n7. Checking Intel oneAPI..." -ForegroundColor Yellow
$oneAPIPath = "${env:ProgramFiles(x86)}\Intel\oneAPI"
if (Test-Path $oneAPIPath) {
    Write-Host "✅ Intel oneAPI found at: $oneAPIPath" -ForegroundColor Green
} else {
    Write-Host "❌ Intel oneAPI not found!" -ForegroundColor Red
    Write-Host "This is required for Intel Arc GPU support." -ForegroundColor Yellow
}

# Summary and recommendations
Write-Host "`n=== Diagnostic Summary ===" -ForegroundColor Cyan

$issues = @()

if (-not $intelGPU) {
    $issues += "Intel GPU drivers not installed"
}

if (-not (Test-Path $oneAPIPath)) {
    $issues += "Intel oneAPI not installed"
}

if ($xpuCheck -like "*XPU is_available: False*") {
    $issues += "XPU not available"
}

if ($issues.Count -eq 0) {
    Write-Host "✅ All checks passed! Intel Arc should be working." -ForegroundColor Green
    Write-Host "Run 'python check_gpu.py' to verify." -ForegroundColor Cyan
} else {
    Write-Host "❌ Issues found:" -ForegroundColor Red
    foreach ($issue in $issues) {
        Write-Host "  - $issue" -ForegroundColor Red
    }
    
    Write-Host "`nRecommended actions:" -ForegroundColor Yellow
    Write-Host "1. Run: .\fix_intel_arc_dependencies.ps1" -ForegroundColor Cyan
    Write-Host "2. Restart your terminal" -ForegroundColor Cyan
    Write-Host "3. Run: conda activate lfp_bot_intel_arc" -ForegroundColor Cyan
    Write-Host "4. Run: python check_gpu.py" -ForegroundColor Cyan
} 