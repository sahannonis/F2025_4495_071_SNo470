# scripts/02_compute_amenity_metrics.py

import os
import geopandas as gpd

DATA_PROCESSED = "data/processed"


def compute_amenity_counts():
    neighborhoods_path = os.path.join(DATA_PROCESSED, "neighborhoods.geojson")
    pois_path = os.path.join(DATA_PROCESSED, "pois.geojson")

    neighborhoods = gpd.read_file(neighborhoods_path).to_crs(epsg=3857)
    pois = gpd.read_file(pois_path).to_crs(epsg=3857)

    # Convert polygons to centroids for point-in-polygon join
    pois["geometry"] = pois.geometry.centroid

    # Spatial join: assign each POI to a neighborhood
    joined = gpd.sjoin(pois, neighborhoods, how="left", predicate="within")

    # Count per neighborhood + category
    counts = joined.groupby(
        ["neighborhood_name", "category"]
    ).size().unstack(fill_value=0)

    for col in ["school", "transit", "mall", "park", "hospital"]:
        if col not in counts.columns:
            counts[col] = 0

    neighborhoods = neighborhoods.merge(
        counts,
        left_on="neighborhood_name",
        right_index=True,
        how="left",
    ).fillna(0)

    # Density metrics (per km²)
    neighborhoods["schools_per_km2"] = neighborhoods["school"] / neighborhoods["area_km2"]
    neighborhoods["transit_per_km2"] = neighborhoods["transit"] / neighborhoods["area_km2"]
    neighborhoods["amenities_per_km2"] = (
        neighborhoods["mall"] + neighborhoods["park"] + neighborhoods["hospital"]
    ) / neighborhoods["area_km2"]

    # Save with geometry
    neighborhoods.to_file(
        os.path.join(DATA_PROCESSED, "neighborhoods_with_amenities.geojson"),
        driver="GeoJSON",
    )

    # And flat metrics for the app
    neighborhoods.drop(columns="geometry").to_parquet(
        os.path.join(DATA_PROCESSED, "neighborhood_metrics.parquet"),
        index=False,
    )

    print("Saved neighborhoods_with_amenities.geojson and neighborhood_metrics.parquet")


def main():
    compute_amenity_counts()


if __name__ == "__main__":
    main()
