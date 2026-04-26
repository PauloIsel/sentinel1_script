from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
import os, shutil
import glob
import json 
import re

# Define a simple data class to hold product information
@dataclass 
class Product:
	name: str
	path: Path
	date: datetime

	def to_json(self) -> str:
		
		return json.dumps(asdict(self), indent=4, default=str)

	@staticmethod
	def list_to_json(products: list['Product']) -> str:
		import json
		from dataclasses import asdict
		return json.dumps([asdict(p) for p in products], indent=4, default=str)


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

		products.append(Product(name=candidate.name, path=candidate, date=acquisition_date))

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


def build_output_file(out_dir: Path, base_name: str) -> Path:
	path = out_dir / base_name
	filesInDir = glob.glob(str(f"{path}*.*"))

	if not filesInDir:
		print(f"Using unique name: {path}")
		return path
	
	if "cache" in str(out_dir):
		print(f"creating cache file {path}...")

		# check if there are any files with the same base name and remove them
		if filesInDir:
			print(f"Warning: {path} already exists. Removing existing file to avoid conflicts.")
			(shutil.rmtree(Path(p)) if Path(p).is_dir() else Path(p).unlink() for p in filesInDir)

		return path

	pattern = re.compile(rf"^{re.escape(base_name)}_(\d{{1,3}})(?:\.[^.]+)?$")
	
	max_idx = 0
	matched_any = False
	existing_names = set(Path(f).stem for f in filesInDir)
	print(existing_names)
	
	for name in existing_names:
		if name == base_name:
			matched_any = True
			continue
			
		match = pattern.search(name)
		if match:
			matched_any = True
			max_idx = max(max_idx, int(match.group(1)))
			
	if not matched_any:
		return path

	next_index = max_idx + 1
	
	new_path = out_dir / f"{base_name}_{next_index:03d}"
	print(f"Warning: files matching '{base_name}' already exist. Using index {next_index:03d} to avoid overwriting.")
	return new_path