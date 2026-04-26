from extractInfo import getExecutable, getProducts, getProductFile, getShapeFile, build_output_file, Product
from dotenv import load_dotenv
from pathlib import Path
import rasterio
import rasterio.plot
import numpy as np
import subprocess
import math
import sys

# Suppress stack traces for cleaner error messages
sys.tracebacklimit = 0

# Load environment variables from .env file
load_dotenv()

# Get the GPT executable path
gpt = getExecutable()


# Define path constants
BASE_PATH = Path(__file__).parent.resolve()
OUT_DIR = BASE_PATH / "out"
DATA_DIR = BASE_PATH / "data"
CACHE_DIR = BASE_PATH / "cache"
PRODUCT_DIR = DATA_DIR / "products"
ROI_DIR = DATA_DIR / "region_of_interest"
WORKFLOW_DIR = BASE_PATH / "workflows"


# # Ensure necessary directories exist
# dirs = [OUT_DIR, DATA_DIR, CACHE_DIR, PRODUCT_DIR, ROI_DIR, WORKFLOW_DIR]
# for d in dirs:
# 	if not d.exists():
# 		print(f"{d} doesn't exist. Creating directory...")
# 		d.mkdir(parents=True, exist_ok=True)


# # Get workflow and products
# productProcessing = WORKFLOW_DIR / "singleProductProcessing.xml"
# products = getProducts(PRODUCT_DIR)
# roi = getShapeFile(ROI_DIR)

gptExec = [
	str(gpt),
	"-x",
	"-J-Xms256m", # Set initial heap size to 256MB
	"-J-Xmx4G", # Set maximum heap size to 2GB
]

# print("Starting pre processing of products...")
# cachedProducts = []
# for product in products:
# 	print(f"Processing product:{product.name}")
# 	product_file = getProductFile(product.path)
# 	print(f"Using product file: {product_file}")
# 	output_file = build_output_file(CACHE_DIR, f"zone_{product.date.strftime('%Y%m%d')}")

# 	cmd = gptExec.copy()
# 	cmd.extend([
# 		str(productProcessing),
# 		f"-Pproduct={str(product_file)}",
# 		f"-Poutput={str(output_file)}",
# 		f"-PvectorFile={str(roi)}",
# 	])

# 	try:
# 		subprocess.run(cmd, check=True)
# 		print(
# 			f"Successfully processed product {product.name}.\n \
# 			Output saved to {output_file}"
# 		)
# 		cachedProducts.append(output_file.with_suffix('.dim'))
# 	except subprocess.CalledProcessError as e:
# 		print(f"Error processing product {product}: \n{e.stderr}")

# print("Finished processing products.")
# stackProducts = WORKFLOW_DIR / "stackProducts.xml"
# out = build_output_file(OUT_DIR, 'flood_zone')

# cmd = gptExec.copy()
# cmd.extend([
# 	str(stackProducts),
# 	f"-Pproduct1={str(cachedProducts[0])}",
# 	f"-Pproduct2={str(cachedProducts[1])}",
# 	f"-Poutput={str(out)}"
# ])


try:
	# print("Stacking products and creating flood mask...")
	# subprocess.run(cmd, check=True)
	# print(f"Flood mask created. Output saved to {out}")
	out = OUT_DIR / "flood_zone"

	res = input("Would you like to visualize the results and calculate the flooded area? (y/n): ")
	if res.lower() == 'n':
		sys.exit(0)
	
	if res.lower() == 'y':
		visualize = WORKFLOW_DIR / "calculateArea.xml"
		image = OUT_DIR / "floodImage"
		tif_path = image.with_suffix('.tif')
		
		run_gpt = True
		if tif_path.exists():
			existing_res = input(f"Existing TIF found ({tif_path.name}). Skip recalculation and use existing file? (y/n): ").strip()
			if existing_res.lower() != 'n':
				run_gpt = False
		
		if run_gpt:
			print(f"Generating flood image TIF, this may take a moment...")
			cmd = gptExec.copy()
			cmd.extend([
				str(visualize),
				f"-Pproduct={str(out.with_suffix('.dim'))}",
				f"-Poutput={str(image)}"
			])
			subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)

		data = rasterio.open(tif_path)
		
		# --- Calculate Flooded Area ---
		band = data.read(1, masked=True)
		# Count the pixels with a value of 1 (the flood indicator we set in our xml expression)
		flood_count = int(np.count_nonzero(band == 1))
		
		# Calculate Area in square meters (approximate for Geographic CRS, exact if Projected)
		if data.crs and data.crs.is_geographic:
			bounds = data.bounds
			center_lat = (bounds.top + bounds.bottom) / 2.0
			lat_rad = math.radians(center_lat)
			
			# Approx. Earth radius in meters
			meters_per_deg_lat = (math.pi / 180.0) * 6378137.0
			meters_per_deg_lon = (math.pi / 180.0) * 6378137.0 * math.cos(lat_rad)
			
			px_area_m2 = abs((data.transform.a * meters_per_deg_lon) * (data.transform.e * meters_per_deg_lat))
		else:
			px_area_m2 = abs(data.transform.a * data.transform.e)
			
		total_area_m2 = flood_count * px_area_m2
		
		print("\n--- Flood Calculation Results ---")
		print(f"Number of Flooded Pixels: {flood_count:,}")
		print(f"Estimated Pixel Size: ~{px_area_m2:,.2f} m²")
		print(f"Total Flooded Area: {total_area_m2:,.2f} m² ({total_area_m2 / 1000000.0:,.3f} km²)\n")

		rasterio.plot.show(data, title="Flood Mask", cmap='Blues')
except subprocess.CalledProcessError as e:
	print(f"Error running workflows: \n{e.stderr}")