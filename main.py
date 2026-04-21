from dotenv import load_dotenv
from datetime import datetime
from pathlib import Path
import subprocess
import re
import os

load_dotenv()

def get_GPT_Executable() -> Path:
	candidates: list[Path] = []

	snap_home = os.environ.get("SNAP_HOME", "C:\\Program Files\\snap")

	if snap_home:
		snap_home_path = Path(snap_home)
		candidates.append(snap_home_path / "bin" / "gpt.exe")

	candidates.extend([
		Path(os.environ.get("ProgramFiles", "")) / "snap" / "bin" / "gpt.exe",
		Path(os.environ.get("ProgramFiles", "")) / "ESA SNAP" / "bin" / "gpt.exe",
	])

	for candidate in candidates:
		if candidate and candidate.exists() and candidate.is_file():
			return candidate

	checked = "\n".join(f"  - {path}" for path in candidates if str(path).strip())
	raise FileNotFoundError(
		"Could not locate SNAP GPT executable.\n"
		"Set SNAP_GPT to gpt.exe, or set SNAP_HOME to your SNAP installation directory.\n"
		"Checked these paths:\n"
		f"{checked if checked else '  - (no candidate paths generated)'}"
	)


def get_Aquisition_Date(product: Path) -> datetime:
	match = re.search(r"_(\d{8}T\d{6})_", product.name)
	if not match:
		raise ValueError(f"Could not parse acquisition time from: {product.name}")
	
	result = datetime.strptime(match.group(1), "%Y%m%dT%H%M%S")

	return result


def discover_products(data: Path) -> list[Path]:
	products: list[tuple[datetime, Path]] = []

	for candidate in data.iterdir():
		is_safe = candidate.is_dir() and candidate.name.upper().endswith(".SAFE")
		is_zip = candidate.is_file() and candidate.suffix.lower() == ".zip"
		if not (is_safe or is_zip):
			continue

		acquisition_start = get_Aquisition_Date(candidate)
		products.append((acquisition_start, candidate))

	if len(products) < 2:
		raise FileNotFoundError("At least two Sentinel-1 products (.SAFE or .zip) are required in data/")

	products.sort(key=lambda item: item[0])
	return [item[1] for item in products]


def resolve_product_input(product: Path) -> Path:
	if product.is_dir() and product.name.upper().endswith(".SAFE"):
		manifest = product / "manifest.safe"
		if not manifest.exists():
			raise FileNotFoundError(f"SAFE manifest not found: {manifest}")
		return manifest
	return product


def resolve_vector_file(data: Path) -> Path:
	preferred = data / "roi.shp"
	if preferred.exists():
		return preferred

	shape_files = sorted(data.glob("*.shp"))
	if not shape_files:
		raise FileNotFoundError("No .shp file found in data/")
	return shape_files[0]


def build_numbered_output_file(out_dir: Path, base_name: str, suffix: str) -> Path:
	index = 1
	while True:
		candidate = out_dir / f"{base_name}_{index:03d}{suffix}"
		if not candidate.exists():
			return candidate
		index += 1


gpt = get_GPT_Executable()
memory = os.environ.get("SNAP_MEMORY", "4G")
BASE_PATH = Path(__file__).parent.resolve()
DATA_DIR = BASE_PATH / "data"

# The workflow XML defines the processing steps for SNAP.
workflowXml = BASE_PATH / "workflow" / "ImageProcessingSentinel1.xml"

# Discover products and determine before/after files based on acquisition time
products = discover_products(DATA_DIR)
before_file = resolve_product_input(products[0])
after_file = resolve_product_input(products[-1])

# Resolve vector file (Region of the flood) - either roi.shp or the first .shp found in data/
vector_file = resolve_vector_file(DATA_DIR)

# Prepare output path with auto-incrementing filename
out_dir = BASE_PATH / "out"
output_file = build_numbered_output_file(out_dir, "floodMaskProcessed", ".dim")
out_dir.mkdir(exist_ok=True)


for required in (gpt, workflowXml, before_file, after_file, vector_file):
	if not required.exists():
		raise FileNotFoundError(f"Required file not found: {required}")

if vector_file.suffix.lower() != ".shp":
	raise ValueError(f"Expected a .shp file, got: {vector_file}")


cmd = [
	str(gpt),
	str(workflowXml),
	f"-PbeforeFile={before_file}",
	f"-PafterFile={after_file}",
	f"-PoutputFile={output_file}",
	f"-PvectorFile={vector_file}",
	"-c",
	memory,
]

print("Command arguments:")
for i, arg in enumerate(cmd):
	print(f"  [{i}] {arg}")

print("Executing SNAP...")
subprocess.run(cmd, check=True)
print("Processing completed successfully")