# Fixed Intel Arc GPU Environment Setup
# This script properly sets up the environment with correct dependency order

# Configuration
$envName = "lfp_bot_intel_arc"
$pythonVersion = "3.11.13"

Write-Host "=== Intel Arc GPU Environment Setup (Fixed) ===" -ForegroundColor Cyan

# Check if Intel GPU drivers are installed
Write-Host "Checking Intel GPU drivers..." -ForegroundColor Yellow
$intelDriver = Get-WmiObject -Class Win32_VideoController | Where-Object { 
    $_.Name -like "*Intel*Arc*" -or 
    $_.Name -like "*Intel*Graphics*" -or 
    $_.Name -like "*Intel*Iris*" 
}
if ($intelDriver) {
    Write-Host "✅ Intel GPU found: $($intelDriver.Name)" -ForegroundColor Green
} else {
    Write-Host "❌ Intel GPU not detected! Please install Intel Arc drivers first." -ForegroundColor Red
    Write-Host "Download from: https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-whql-windows.html" -ForegroundColor Yellow
    exit 1
}

# Remove existing environment if exists
Write-Host "Removing existing environment if exists..." -ForegroundColor Yellow
conda env remove -n $envName -y

# Create new environment
Write-Host "Creating new environment '$envName' with Python $pythonVersion..." -ForegroundColor Cyan
conda create -n $envName python=$pythonVersion -y

# Step 1: Install PyTorch CPU first (required for Intel Extension)
Write-Host "Step 1: Installing PyTorch CPU..." -ForegroundColor Cyan
conda run -n $envName pip install torch==2.1.0 torchvision==0.16.0 torchaudio==2.1.0 --index-url https://download.pytorch.org/whl/cpu

# Step 2: Install Intel Extension for PyTorch
Write-Host "Step 2: Installing Intel Extension for PyTorch..." -ForegroundColor Cyan
conda run -n $envName pip install intel-extension-for-pytorch==2.1.40

# Step 3: Install Intel Extension for Transformers
Write-Host "Step 3: Installing Intel Extension for Transformers..." -ForegroundColor Cyan
conda run -n $envName pip install intel-extension-for-transformers==1.4.2

# Step 4: Install other requirements
Write-Host "Step 4: Installing other requirements..." -ForegroundColor Cyan
conda run -n $envName pip install -r requirements_intel_arc_fixed.txt

# Step 5: Install additional Intel dependencies
Write-Host "Step 5: Installing additional Intel dependencies..." -ForegroundColor Cyan
conda run -n $envName pip install intel-cmplr-lib-rt intel-sycl-rt pytorch-triton-xpu

# Create .env file if not exists
$envFile = ".\.env"
if (-not (Test-Path $envFile)) {
    @"
# Telegram Bot
TELEGRAM_TOKEN=your_telegram_token

# Hugging Face
HUGGINGFACEHUB_API_TOKEN=your_hf_token
MODEL_NAME=Qwen/Qwen2-1.5B-Instruct
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Device configuration for Intel Arc
DEVICE=xpu
XPU_DEVICE_ID=0

# Database
CHROMA_DB_PATH=./chroma_db

# Intel XPU specific settings
INTEL_EXTENSION_FOR_PYTORCH_VERBOSE=1
SYCL_PI_LEVEL_ZERO_USE_IMMEDIATE_COMMANDLISTS=1
ONEAPI_DEVICE_SELECTOR=level_zero:gpu
"@ | Out-File -FilePath $envFile -Encoding utf8
    Write-Host "Created .env file with Intel Arc settings. Please update it with your tokens." -ForegroundColor Yellow
} else {
    Write-Host ".env file already exists. Please ensure DEVICE=xpu is set." -ForegroundColor Yellow
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Green
Write-Host "To activate the environment, run:" -ForegroundColor Cyan
Write-Host "conda activate $envName" -ForegroundColor White
Write-Host "`nTo test Intel XPU support, run:" -ForegroundColor Cyan
Write-Host "python check_gpu.py" -ForegroundColor White
Write-Host "`nIf XPU is still not available, run:" -ForegroundColor Cyan
Write-Host ".\fix_intel_arc_dependencies.ps1" -ForegroundColor White 