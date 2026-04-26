# Sentinel-1 Flood Detection Script - Setup for Windows
# This script automates the setup process for the Sentinel-1 analysis workflow

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Sentinel-1 Script Setup" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "1. Checking Python installation..." -ForegroundColor Yellow
python --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ from https://www.python.org/" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Python found" -ForegroundColor Green
Write-Host ""

# Create virtual environment
Write-Host "2. Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path ".venv") {
    Write-Host "   Virtual environment already exists, skipping creation" -ForegroundColor Gray
} else {
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to create virtual environment" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Virtual environment created" -ForegroundColor Green
}
Write-Host ""

# Activate virtual environment
Write-Host "3. Activating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1
Write-Host "✓ Virtual environment activated" -ForegroundColor Green
Write-Host ""

# Install requirements
Write-Host "4. Installing Python dependencies..." -ForegroundColor Yellow
pip install --upgrade pip --quiet
pip install -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Dependencies installed" -ForegroundColor Green
Write-Host ""

# Create .env file if it doesn't exist
Write-Host "5. Setting up environment configuration..." -ForegroundColor Yellow
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "   ⚠ .env file created from .env.example" -ForegroundColor Yellow
    Write-Host "   Please edit .env and update SNAP_DIRECTORY with your SNAP installation path" -ForegroundColor Yellow
    Write-Host "   (example: C:\Program Files\esa-snap)" -ForegroundColor Yellow
} else {
    Write-Host "   .env file already exists" -ForegroundColor Gray
}
Write-Host ""

# Detect SNAP installation
Write-Host "6. Detecting SNAP installation..." -ForegroundColor Yellow
$snapPaths = @(
    "C:\Program Files\esa-snap"
)

if (Test-Path ".env") {
    Get-Content ".env" | Where-Object { $_ -match '=' -and $_ -notmatch '^\s*#' } | foreach {
        $name, $value = $_.Split('=', 2)
        Set-Item -Path "env:$($name.Trim())" -Value $value.Trim()
    }
}

if ($env:SNAP_DIRECTORY) {
    # Put the env dir at the front of the list
    $snapPaths = @($env:SNAP_DIRECTORY) + $snapPaths
}


$snapFound = $false
foreach ($path in $snapPaths) {
    echo "Checking: $path"
    if (Test-Path "$path\bin\gpt.exe") {
        Write-Host "   ✓ Found SNAP at: $path" -ForegroundColor Green
        $snapFound = $true
        $SNAP_DIR = $path
        break
    }
}

if (-not $snapFound) {
    Write-Host "   ⚠ SNAP not found in default locations" -ForegroundColor Yellow
    Write-Host "   Please ensure SNAP is installed and update SNAP_DIRECTORY in .env" -ForegroundColor Yellow
}

Write-Host ""

# Create data directories
Write-Host "7. Creating data directories..." -ForegroundColor Yellow
@("data", "data\products", "data\region_of_interest", "out", "cache") | ForEach-Object {
    if (-not (Test-Path $_)) {
        New-Item -ItemType Directory -Path $_ -Force | Out-Null
        Write-Host "   Created: $_" -ForegroundColor Green
    } else {
        Write-Host "   Already exists: $_" -ForegroundColor Gray
    }
}
Write-Host ""

# Summary
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Edit .env and verify SNAP_DIRECTORY points to your SNAP installation" -ForegroundColor White
Write-Host "2. Add Sentinel-1 products to: data\products\" -ForegroundColor White
Write-Host "3. Add a region of interest shapefile to: data\region_of_interest\" -ForegroundColor White
Write-Host "4. Run: python main.py" -ForegroundColor White
Write-Host ""
Write-Host "For more information, see SETUP.md" -ForegroundColor Gray
Write-Host ""
