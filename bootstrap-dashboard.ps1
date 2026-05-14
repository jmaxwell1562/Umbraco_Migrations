param(
    [string]$VenvPath = '.venv',
    [switch]$SkipStart
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$workspaceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $workspaceRoot

function Write-Step {
    param([string]$Message)
    Write-Host "`n==> $Message" -ForegroundColor Cyan
}

function Get-SystemPython {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return $pythonCommand.Source
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand) {
        return "$($pyCommand.Source) -3"
    }

    throw 'Python was not found in PATH. Install Python 3.10+ and rerun this script.'
}

$systemPython = Get-SystemPython
$resolvedVenvPath = Join-Path $workspaceRoot $VenvPath
$venvPython = Join-Path $resolvedVenvPath 'Scripts\python.exe'

Write-Step 'Checking Python'
Write-Host "Using Python launcher: $systemPython"

if (-not (Test-Path $venvPython)) {
    Write-Step "Creating virtual environment at $resolvedVenvPath"
    if ($systemPython -like '*py.exe -3') {
        & py -3 -m venv $resolvedVenvPath
    } else {
        & python -m venv $resolvedVenvPath
    }
}

if (-not (Test-Path $venvPython)) {
    throw "Virtual environment was not created successfully at $resolvedVenvPath"
}

Write-Step 'Upgrading pip'
& $venvPython -m pip install --upgrade pip

Write-Step 'Installing bootstrap build tools'
& $venvPython -m pip install --upgrade setuptools wheel

Write-Step 'Installing Python dependencies'
& $venvPython -m pip install -r requirements.txt

Write-Step 'Installing Playwright Chromium'
& $venvPython -m playwright install chromium

Write-Step 'Bootstrap complete'
Write-Host "Virtual environment: $resolvedVenvPath"
Write-Host 'Dashboard URL: http://localhost:5000'

if (-not $SkipStart) {
    Write-Step 'Starting dashboard'
    & $venvPython app.py
} else {
    Write-Host 'SkipStart specified. Dashboard was not launched.' -ForegroundColor Yellow
}