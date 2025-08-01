# Script to start the Telegram bot with environment check and activation
# Place this file in your project root directory

# Configuration
$envName = "lfp_bot_py311"
$projectPath = $PSScriptRoot
$requiredPythonVersion = "3.11"
$logFile = Join-Path -Path $projectPath -ChildPath "bot_startup.log"

# Function to write to log file and console
function Write-Log {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logMessage = "[$timestamp] [$Level] $Message"
    
    # Write to console with colors
    switch ($Level) {
        "ERROR" { Write-Host $logMessage -ForegroundColor Red }
        "WARN"  { Write-Host $logMessage -ForegroundColor Yellow }
        "INFO"  { Write-Host $logMessage -ForegroundColor Cyan }
        "DEBUG" { Write-Host $logMessage -ForegroundColor Gray }
        default { Write-Host $logMessage }
    }
    
    # Write to log file
    Add-Content -Path $logFile -Value $logMessage -ErrorAction SilentlyContinue
}

# Function to check if conda environment exists and has correct Python version
function Test-CondaEnvExists {
    param($envName, $requiredVersion)
    try {
        Write-Log "Checking for Conda environment '$envName'..." -Level "DEBUG"
        $envs = conda env list --json | ConvertFrom-Json
        $envPath = $envs.envs | Where-Object { $_ -match "\\$envName$" }
        
        if (-not $envPath) {
            Write-Log "Conda environment '$envName' not found." -Level "WARN"
            return $false
        }
        
        Write-Log "Found environment at: $envPath" -Level "DEBUG"
        
        # Check Python version in the environment
        Write-Log "Checking Python version in environment..." -Level "DEBUG"
        $pythonVersion = conda run -n $envName python --version 2>&1 | ForEach-Object { $_ -replace '[^0-9.]' } | ForEach-Object { $_.Trim() }
        
        Write-Log "Environment has Python $pythonVersion" -Level "DEBUG"
        
        if ($pythonVersion -notlike "$requiredVersion*") {
            Write-Log "Environment '$envName' has Python $pythonVersion, but Python $requiredVersion is required." -Level "WARN"
            return $false
        }
        
        Write-Log "Conda environment check passed" -Level "DEBUG"
        return $true
    } catch {
        Write-Log "Error checking conda environment: $_" -Level "ERROR"
        return $false
    }
}

# Function to check if a package is installed
function Test-PackageInstalled {
    param($packageName)
    try {
        $basePkg = ($packageName -split '[<>=!]')[0]
        Write-Log "Checking if package '$basePkg' is installed..." -Level "DEBUG"
        
        $installed = conda run -n $envName pip list --format=json | ConvertFrom-Json | Where-Object { $_.name -eq $basePkg }
        $isInstalled = [bool]$installed
        
        if ($isInstalled) {
            Write-Log "Package '$basePkg' is installed (version: $($installed.version))" -Level "DEBUG"
        } else {
            Write-Log "Package '$basePkg' is not installed" -Level "DEBUG"
        }
        
        return $isInstalled
    } catch {
        Write-Log "Error checking package '$basePkg': $_" -Level "ERROR"
        return $false
    }
}

# Function to install package
function Install-Package {
    param($packageName)
    try {
        $basePkg = ($packageName -split '[<>=!]')[0]
        Write-Log "Installing package: $packageName" -Level "INFO"
        
        $output = conda run -n $envName pip install $packageName 2>&1
        if ($LASTEXITCODE -ne 0) {
            Write-Log "Failed to install $basePkg. Error: $output" -Level "ERROR"
            return $false
        }
        
        Write-Log "Successfully installed $basePkg" -Level "INFO"
        return $true
    } catch {
        Write-Log "Error installing package '$basePkg': $_" -Level "ERROR"
        return $false
    }
}

# Function to check and create required directories
function Initialize-Environment {
    try {
        # Create logs directory if it doesn't exist
        $logsDir = Join-Path -Path $projectPath -ChildPath "logs"
        if (-not (Test-Path $logsDir)) {
            New-Item -ItemType Directory -Path $logsDir | Out-Null
            Write-Log "Created logs directory: $logsDir" -Level "DEBUG"
        }
        
        # Create data directory if it doesn't exist
        $dataDir = Join-Path -Path $projectPath -ChildPath "data"
        if (-not (Test-Path $dataDir)) {
            New-Item -ItemType Directory -Path $dataDir | Out-Null
            Write-Log "Created data directory: $dataDir" -Level "DEBUG"
        }
        
        return $true
    } catch {
        Write-Log "Error initializing environment: $_" -Level "ERROR"
        return $false
    }
}

# Main execution
try {
    # Initialize log file
    "=== Bot Startup Log ===" | Out-File -FilePath $logFile -Force
    Write-Log "=== Starting LFP-TGbot-LLM-RAG ===" -Level "INFO"
    Write-Log "Project path: $projectPath" -Level "INFO"
    
    # Check if running as administrator (for port binding if needed)
    $isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    if ($isAdmin) {
        Write-Log "Running with administrator privileges" -Level "WARN"
    }
    
    # Check if conda is available
    Write-Log "Checking if Conda is available..." -Level "INFO"
    if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
        Write-Log "Error: Conda is not available. Please install Miniconda/Anaconda first." -Level "ERROR"
        Write-Log "Download from: https://docs.conda.io/en/latest/miniconda.html" -Level "INFO"
        exit 1
    }
    
    # Check if environment exists and has correct Python version
    if (-not (Test-CondaEnvExists -envName $envName -requiredVersion $requiredPythonVersion)) {
        Write-Log "Error: Conda environment '$envName' with Python $requiredPythonVersion not found." -Level "ERROR"
        Write-Log "Please run 'setup_env.ps1' first to create the environment." -Level "INFO"
        exit 1
    }
    
    # Initialize required directories
    if (-not (Initialize-Environment)) {
        Write-Log "Failed to initialize required directories" -Level "ERROR"
        exit 1
    }
    
    # List of required packages with versions
    $requiredPackages = @(
        "python-telegram-bot>=20.0",
        "python-dotenv>=0.19.0",
        "torch>=2.0.0",
        "transformers>=4.30.0",
        "sentence-transformers>=2.2.2",
        "chromadb>=0.4.0",
        "langchain>=0.0.200",
        "accelerate>=0.20.0",
        "flask>=2.0.0",
        "flask-sqlalchemy>=3.0.0",
        "huggingface-hub>=0.15.0",
        "intel-extension-for-transformers"
    )
    
    # Check and install missing packages
    $missingPackages = @()
    foreach ($pkg in $requiredPackages) {
        if (-not (Test-PackageInstalled -packageName $pkg)) {
            $missingPackages += $pkg
        }
    }
    
    # Install missing packages if any
    if ($missingPackages.Count -gt 0) {
        Write-Log "Found $($missingPackages.Count) missing package(s) to install" -Level "INFO"
        foreach ($pkg in $missingPackages) {
            if (-not (Install-Package -packageName $pkg)) {
                Write-Log "Failed to install required package: $pkg" -Level "ERROR"
                exit 1
            }
        }
        Write-Log "All required packages installed successfully" -Level "INFO"
    } else {
        Write-Log "All required packages are already installed" -Level "INFO"
    }
    
    # Check if .env file exists
    $envFile = Join-Path -Path $projectPath -ChildPath ".env"
    if (-not (Test-Path $envFile)) {
        $envExample = Join-Path -Path $projectPath -ChildPath ".env.example"
        if (Test-Path $envExample) {
            Write-Log "Creating .env file from .env.example" -Level "INFO"
            Copy-Item -Path $envExample -Destination $envFile -Force
            Write-Log "Please update the .env file with your configuration and restart the bot" -Level "WARN"
            if (-not $isAdmin) {
                Start-Process notepad $envFile -Wait
            }
            exit 1
        } else {
            Write-Log "Error: .env file not found and no .env.example available" -Level "ERROR"
            Write-Log "Please create a .env file with your configuration" -Level "INFO"
            exit 1
        }
    }
    
    # Start the bot
    Write-Log "Starting the bot..." -Level "INFO"
    Set-Location $projectPath
    
    # Log the command being executed
    $command = "conda run -n $envName python bot.py"
    Write-Log "Executing: $command" -Level "DEBUG"
    
    # Start the bot process
    $process = Start-Process -FilePath "conda" -ArgumentList "run -n $envName python bot.py" -NoNewWindow -PassThru
    $processId = $process.Id
    
    Write-Log "Bot started with process ID: $processId" -Level "INFO"
    Write-Log "Bot is now running. Check the logs in the 'logs' directory for details." -Level "INFO"
    
    # Wait for the process to complete
    $process.WaitForExit()
    $exitCode = $process.ExitCode
    
    if ($exitCode -ne 0) {
        Write-Log "Bot process exited with error code: $exitCode" -Level "ERROR"
        exit $exitCode
    }
    
} catch {
    Write-Log "An unexpected error occurred: $_" -Level "ERROR"
    Write-Log $_.ScriptStackTrace -Level "ERROR"
    exit 1
} finally {
    Write-Log "Bot process ended" -Level "INFO"
}

# Keep the window open if running directly (not from shortcut)
if ($MyInvocation.MyCommand.CommandType -ne "ExternalScript") {
    Write-Host "`nPress any key to exit..." -ForegroundColor Cyan
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
