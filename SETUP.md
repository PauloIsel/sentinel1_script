# Setup Guide

This guide helps you set up the Sentinel-1 flood detection script on your machine.

## Prerequisites

- **Python 3.8+**
- **SNAP (ESA Sentinel Application Platform)** - Download from [step.esa.int](https://step.esa.int/main/download/snap-download/)

## Automatic Setup (Recommended)

### Windows (PowerShell)
```powershell
cd path\to\sentinel1_script
.\setup.ps1
```

### Linux/macOS (Bash)
```bash
cd path/to/sentinel1_script
chmod +x setup.sh
./setup.sh
```

## Manual Setup

### Step 1: Create and activate a virtual environment

```powershell
# Windows - PowerShell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

```bash
# Linux/macOS
python3 -m venv .venv
source .venv/bin/activate
```

### Step 2: Install Python dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Configure environment variables

Copy `.env.example` to `.env` and update the paths for your machine:

```bash
cp .env.example .env  # Linux/macOS
copy .env.example .env  # Windows
```

Edit `.env` and set:
- **SNAP_DIRECTORY**: Path to your SNAP installation directory
  - Windows: `C:\Program Files\esa-snap`
  - Linux/macOS: `/opt/snap` or similar

### Step 4: Prepare input data

Place your data in the `data/` directory:
- **Sentinel-1 products** (.SAFE directories or .zip files): `data/products/`
- **Region of Interest shapefile** (.shp file): `data/region_of_interest/`

### Step 5: Run the script

```bash
python main.py
```

## Troubleshooting

### "SNAP_DIRECTORY environment variable is not set" error
Ensure you've created `.env` from `.env.example` and set the `SNAP_DIRECTORY` path correctly.

### "No products found in data/" error
Add at least two Sentinel-1 products (.SAFE or .zip) to `data/products/` directory.

### "No .shp file found" error
Add a region of interest shapefile (.shp) to `data/region_of_interest/` directory.
