# Setup script for Intel Arc GPU optimized environment
# This script sets up the environment with proper Intel XPU support

# Configuration
$envName = "lfp_bot_intel_arc"
$pythonVersion = "3.11.13"

Write-Host "=== Intel Arc GPU Environment Setup ===" -ForegroundColor Cyan

# Check if Intel GPU drivers are installed
Write-Host "Checking Intel GPU drivers..." -ForegroundColor Yellow
$intelDriver = Get-WmiObject -Class Win32_VideoController | Where-Object { $_.Name -like "*Intel*Arc*" -or $_.Name -like "*Intel*Graphics*" }
if ($intelDriver) {
    Write-Host "Intel GPU found: $($intelDriver.Name)" -ForegroundColor Green
} else {
    Write-Host "Warning: Intel GPU not detected. Please install Intel Arc drivers." -ForegroundColor Red
    Write-Host "Download from: https://www.intel.com/content/www/us/en/download/785597/intel-arc-iris-xe-graphics-whql-windows.html" -ForegroundColor Yellow
}

# Remove existing environment if exists
Write-Host "Removing existing environment if exists..." -ForegroundColor Yellow
conda env remove -n $envName -y

# Create new environment
Write-Host "Creating new environment '$envName' with Python $pythonVersion..." -ForegroundColor Cyan
conda create -n $envName python=$pythonVersion -y

# Activate and install Intel-optimized PyTorch
Write-Host "Installing Intel-optimized PyTorch..." -ForegroundColor Cyan
conda run -n $envName pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Install Intel Extension for PyTorch
Write-Host "Installing Intel Extension for PyTorch..." -ForegroundColor Cyan
conda run -n $envName pip install intel-extension-for-pytorch

# Install Intel Extension for Transformers
Write-Host "Installing Intel Extension for Transformers..." -ForegroundColor Cyan
conda run -n $envName pip install intel-extension-for-transformers

# Install other requirements
Write-Host "Installing other requirements..." -ForegroundColor Cyan
conda run -n $envName pip install -r requirements_intel_arc.txt

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