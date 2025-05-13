# Check if in the python environment
$pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Path
Write-Host "PYTHON_PATH: $pythonPath"

if (-not $pythonPath) {
    Write-Host "Error: Python not found in PATH" -ForegroundColor Red
    exit 1
}

$pythonEnvFolder = Split-Path -Parent (Split-Path -Parent $pythonPath)
$pythonActiveFile = Join-Path $pythonEnvFolder "Scripts\activate.ps1"

if (-not (Test-Path $pythonActiveFile)) {
    Write-Host "Python active file does not exist: $pythonActiveFile" -ForegroundColor Red
    Write-Host "Error: Please activate the python environment first." -ForegroundColor Red
    exit 1
}

# Construct the full path to the .azdev\env_config directory
$azdevEnvConfigFolder = Join-Path $env:USERPROFILE ".azdev\env_config"
Write-Host "AZDEV_ENV_CONFIG_FOLDER: $azdevEnvConfigFolder"

# Check if the directory exists
if (-not (Test-Path $azdevEnvConfigFolder)) {
    Write-Host "AZDEV_ENV_CONFIG_FOLDER does not exist: $azdevEnvConfigFolder" -ForegroundColor Red
    Write-Host "Error: azdev environment is not completed, please run 'azdev setup' first." -ForegroundColor Red
    exit 1
}

$configFile = Join-Path $azdevEnvConfigFolder ($pythonEnvFolder.Substring(2) + "\config")
if (-not (Test-Path $configFile)) {
    Write-Host "CONFIG_FILE does not exist: $configFile" -ForegroundColor Red
    Write-Host "Error: azdev environment is not completed, please run 'azdev setup' first." -ForegroundColor Red
    exit 1
}

Write-Host "CONFIG_FILE: $configFile"

exit 0