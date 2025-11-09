# scripts/03_merge_rent_data.py

import os
import sys

try:
    import pandas as pd
    import geopandas as gpd
except ImportError as e:
    print(f"Error importing required packages: {e}")
    sys.exit(1)

# Check for openpyxl which is required for reading Excel files
try:
    import openpyxl
except ImportError:
    print("ERROR: openpyxl is required to read Excel files.")
    print("Please install it using: pip install openpyxl")
    print("Or: python -m pip install openpyxl")
    sys.exit(1)

DATA_RAW = "data/raw"
DATA_PROCESSED = "data/processed"


def load_vancouver_avg_rent_2024():
    """
    Read CMHC Rental Market Survey (rmr-canada-2024-en.xlsx)
    and extract the 2024 average rent for Vancouver CMA
    from Table 6.0.
    """
    path = os.path.join(DATA_RAW, "rmr-canada-2024-en.xlsx")
    xls = pd.ExcelFile(path)
    df = xls.parse("Table 6.0", header=None)

    # Find the row for "Vancouver CMA" in first column
    mask = df[0].astype(str).str.contains("Vancouver CMA", na=False)
    row = df[mask].iloc[0]

    # Column 4 in this table is the 2024 average rent for apartment structures
    avg_rent_2024 = float(row[4])
    return avg_rent_2024


def merge_rent():
    neighborhoods = gpd.read_file(
        os.path.join(DATA_PROCESSED, "neighborhoods_with_amenities.geojson")
    )

    avg_rent = load_vancouver_avg_rent_2024()
    neighborhoods["avg_rent"] = avg_rent  # same CMA average for all neighborhoods

    neighborhoods.to_file(
        os.path.join(DATA_PROCESSED, "neighborhoods_full.geojson"),
        driver="GeoJSON",
    )

    neighborhoods.drop(columns="geometry").to_parquet(
        os.path.join(DATA_PROCESSED, "neighborhood_metrics.parquet"),
        index=False,
    )

    print(f"Merged Vancouver CMA avg rent (2024) = ${avg_rent:.0f}")


def main():
    merge_rent()


if __name__ == "__main__":
    main()
