# Script to start the Telegram bot with environment check and activation
# Place this file in your project root directory and create a shortcut to it in the Startup folder

# Configuration
$envName = "lfp_bot_py311"
$projectPath = $PSScriptRoot

# Function to check if conda environment exists
function Test-CondaEnvExists {
    param($envName)
    try {
        $envs = conda env list --json | ConvertFrom-Json
        return $envs.envs -match $envName -or $envs.envs -match [regex]::Escape($envName)
    } catch {
        return $false
    }
}

# Function to check if a package is installed
function Test-PackageInstalled {
    param($packageName)
    try {
        $installed = conda run -n $envName pip list --format=json | ConvertFrom-Json | Where-Object { $_.name -eq $packageName }
        return [bool]$installed
    } catch {
        return $false
    }
}

# Main execution
try {
    Write-Host "=== Starting LFP-TGbot-LLM-RAG ===" -ForegroundColor Cyan
    
    # Check if conda is available
    if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
        Write-Host "Error: Conda is not available. Please install Miniconda/Anaconda first." -ForegroundColor Red
        exit 1
    }
    
    # Check if environment exists
    if (-not (Test-CondaEnvExists -envName $envName)) {
        Write-Host "Error: Conda environment '$envName' not found." -ForegroundColor Red
        Write-Host "Please run 'setup_env.ps1' first to create the environment." -ForegroundColor Yellow
        exit 1
    }
    
    # Check for required packages
    $requiredPackages = @("python-telegram-bot", "python-dotenv")
    $missingPackages = @()
    
    foreach ($pkg in $requiredPackages) {
        if (-not (Test-PackageInstalled -packageName $pkg)) {
            $missingPackages += $pkg
        }
    }
    
    # Install missing packages if any
    if ($missingPackages.Count -gt 0) {
        Write-Host "Installing missing packages: $($missingPackages -join ', ')" -ForegroundColor Yellow
        foreach ($pkg in $missingPackages) {
            conda run -n $envName pip install $pkg
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Failed to install $pkg" -ForegroundColor Red
                exit 1
            }
        }
    }
    
    # Check if .env file exists
    $envFile = Join-Path -Path $projectPath -ChildPath ".env"
    if (-not (Test-Path $envFile)) {
        Write-Host "Error: .env file not found. Please create one with your configuration." -ForegroundColor Red
        exit 1
    }
    
    # Start the bot
    Write-Host "Starting the bot..." -ForegroundColor Green
    Set-Location $projectPath
    conda run -n $envName python bot.py
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "Error: Failed to start the bot (exit code: $LASTEXITCODE)" -ForegroundColor Red
        exit $LASTEXITCODE
    }
    
} catch {
    Write-Host "An error occurred: $_" -ForegroundColor Red
    exit 1
}

# Keep the window open if running directly (not from shortcut)
if ($MyInvocation.MyCommand.CommandType -ne "ExternalScript") {
    Write-Host "`nPress any key to exit..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
