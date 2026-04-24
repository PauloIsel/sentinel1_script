from dataclasses import dataclass
from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
import subprocess
import sys
import re
import os

# Suppress stack traces for cleaner error messages
sys.tracebacklimit = 0

# Load environment variables from .env file
load_dotenv()


# Define a simple data class to hold product information
@dataclass 
class Product:
	path: Path
	date: datetime


# Function to locate the SNAP GPT executable
def getExecutable() -> Path:
	print("Locating SNAP GPT executable...")
	snap_dir = os.getenv("SNAP_DIRECTORY")

	# If SNAP_DIRECTORY is set, check if gpt.exe exists there
	if snap_dir:
		candidate = Path(snap_dir)
		gpt_exec = candidate / "bin" / "gpt.exe"

		if gpt_exec.exists():
			print(f"Found gpt.exe at: {gpt_exec}")
			return gpt_exec
		
		raise FileNotFoundError(
			f"SNAP_DIRECTORY is set to '{snap_dir}', but gpt.exe was not found.\n"
			"Verify SNAP_DIRECTORY in your .env points to the SNAP installation root."
		)

	raise FileNotFoundError(
		"SNAP_DIRECTORY environment variable is not set.\n"
		"Please set SNAP_DIRECTORY in your .env to your SNAP installation directory,\n"
		"or install SNAP at the default location: C:\\Program Files\\snap."
	)


def getDate(product: Path) -> datetime:
	match = re.search(r"_(\d{8}T\d{6})_", product.name)
	if not match:
		raise ValueError(f"Could not parse acquisition time from: {product.name}")
	
	result = datetime.strptime(match.group(1), "%Y%m%dT%H%M%S")
	print(f"Extracted acquisition time: {result} from {product.name}")
	return result


def getProducts(data: Path) -> list[Product]:
	print("Discovering products...")

	entries = list(data.iterdir())

	if not entries:
		raise FileNotFoundError(
			"No products found in data/.\n"
			"Please add at least two Sentinel-1 products (.SAFE or .zip) to the data/products/ directory."
		)

	valid_candidates: list[Path] = []

	for candidate in entries:
		is_safe = candidate.is_dir() and candidate.name.upper().endswith(".SAFE")
		is_zip = candidate.is_file() and candidate.suffix.lower() == ".zip"
		if is_safe or is_zip:
			valid_candidates.append(candidate)
		else:
			print(
				f"Invalid product found in data/: {candidate.name}.\n"
				"Expected .SAFE directory or .zip file."
			)


	if len(valid_candidates) < 2:
		raise FileNotFoundError(
			"At least two Sentinel-1 products (.SAFE or .zip) " \
			"are required in data/products/ folder."
		)


	# If there are more than two valid products, ask the user to select two.
	selected_candidates: list[Path]
	if len(valid_candidates) > 2:
		print("More than two valid products found. Please select two to use:")
		for i, cand in enumerate(valid_candidates, start=1):
			print(f"	[{i}] {cand.name}")

		while True:
			choice = input("Enter two numbers separated by a comma (e.g. 1,3): ")
			parts = re.split(r"\s*,\s*", choice.strip())

			if len(parts) != 2:
				print("Please enter exactly two numbers separated by a comma.")
				continue

			# Validate that both parts are integers
			try:
				idxs = [int(p) for p in parts]
			except ValueError:
				print("Invalid input. Use numbers like '1,2'.")
				continue

			# Validate that the numbers are within the valid range
			if any(i not in range(1, len(valid_candidates) + 1) for i in idxs):
				print("One or more numbers are out of range. Try again.")
				continue

			if idxs[0] == idxs[1]:
				print("Please select two different products.")
				continue

			selected_candidates = [valid_candidates[i - 1] for i in idxs]
			break
	else:
		selected_candidates = valid_candidates

	products: list[Product] = []
	for candidate in selected_candidates:
		acquisition_date = getDate(candidate)

		products.append(Product(path=candidate, date=acquisition_date))

	products.sort(key=lambda p: p.date)
	return products


def getProductFile(product: Path) -> Path:
	# If it's a .SAFE directory, return the manifest.safe file inside it
	if product.is_dir() and product.name.upper().endswith(".SAFE"):
		manifest = product / "manifest.safe"
		if not manifest.exists():
			raise FileNotFoundError(f"SAFE manifest not found: {manifest}")
		return manifest
	
	# If it's a .zip file, return it directly
	return product


def getShapeFile(data: Path) -> Path:
	# Look for .shp files in the specified directory
	shape_files = sorted(data.glob("*.shp"))

	if not shape_files:
		raise FileNotFoundError(
			"No .shp file found in data/region_of_interest/. " \
			"Please add a shapefile to this directory."
		)
	
	if len(shape_files) > 1:
		print("Multiple .shp files found in data/region_of_interest. Please select one:")
		for i, shp in enumerate(shape_files, start=1):
			print(f"	[{i}] {shp.name}")

		while True:
			choice = input("Enter the number of the desired .shp file: ")
			try:
				idx = int(choice.strip())
				if idx not in range(1, len(shape_files) + 1):
					print("Number out of range. Try again.")
					continue
				return shape_files[idx - 1]
			except ValueError:
				print("Invalid input. Please enter a number.")

	return shape_files[0]


def build_numbered_output_file(out_dir: Path, base_name: str, suffix: str) -> Path:
	index = 1
	while True:
		candidate = out_dir / f"{base_name}_{index:03d}{suffix}"
		if not candidate.exists():
			return candidate
		index += 1


gpt = getExecutable()

memory = os.getenv("SNAP_MEMORY")

if memory is None:
	memory = "4G" # Default value if not set in .env


# Get current folder path
BASE_PATH = Path(__file__).parent.resolve()

# Define data directory path
DATA_DIR = BASE_PATH / "data"
if not DATA_DIR.exists():
	# create the directory if it doesn't exist
	DATA_DIR.mkdir(parents=True)

PRODUCT_DIR = DATA_DIR / "products"
print (f"Checking for products in: {PRODUCT_DIR}")
if not PRODUCT_DIR.exists():
	# create the directory if it doesn't exist
	PRODUCT_DIR.mkdir(parents=True)
	print(f"Created products directory at: {PRODUCT_DIR}\nPlease add Sentinel-1 products (.SAFE or .zip) to this folder and rerun the program.")
	sys.exit(1)


# Get workflow XML path
workflowXml = BASE_PATH / "workflow" / "ImageProcessingSentinel1.xml"

# Discover products and determine before/after files based on acquisition time
products = getProducts(PRODUCT_DIR)

if (products[0].date == products[1].date):
	raise ValueError(
		f"Selected products have the same acquisition time: {products[0].date}.\n"
		"Please choose two products with different acquisition times."
	)

before_file = getProductFile(products[0].path)
after_file = getProductFile(products[1].path)

ROI_DIR = DATA_DIR / "region_of_interest"
if not ROI_DIR.exists():
	ROI_DIR.mkdir(parents=True)
	print(f"Created region_of_interest directory at: {ROI_DIR}\nPlease add a shapefile (.shp) to this folder and rerun the program.")
	sys.exit(1)

# Get the study region shapefile
regionOfInterest = getShapeFile(ROI_DIR)

if regionOfInterest.suffix.lower() != ".shp":
	raise ValueError(f"Expected a .shp file, got: {regionOfInterest}")

# Prepare output path with auto-incrementing filename
out_dir = BASE_PATH / "out"
output_file = build_numbered_output_file(out_dir, "floodMaskProcessed", ".dim")
out_dir.mkdir(exist_ok=True)

programVars = [gpt, workflowXml, before_file, after_file, regionOfInterest]
for required in programVars:
	if not required.exists():
		raise FileNotFoundError(f"Required file not found: {required}")


cmd = [
	str(gpt),
	str(workflowXml),
	f"-PbeforeFile={before_file}",
	f"-PafterFile={after_file}",
	f"-PoutputFile={output_file}",
	f"-PvectorFile={regionOfInterest}",
	"-c",
	memory,
]

print("Command arguments:")
for i, arg in enumerate(cmd):
	print(f"  [{i}] {arg}")

print("Executing SNAP...")
subprocess.run(cmd, check=True)
print(f"Processing complete. Output saved to: {output_file}")