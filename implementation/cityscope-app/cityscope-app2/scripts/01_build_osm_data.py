# scripts/01_build_osm_data.py

import os
import osmnx as ox
import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon, box

DATA_PROCESSED = "data/processed"
CITY_NAME = "Vancouver, British Columbia, Canada"  # study area


def get_city_boundary():
    """
    Download city boundary polygon in WGS84 (lat/lon).

    IMPORTANT:
    - We keep this in the default CRS for OSMnx (EPSG:4326).
    - We only project AFTER downloading features.
    """
    city_gdf = ox.geocode_to_gdf(CITY_NAME)  # usually EPSG:4326
    polygon = city_gdf.geometry.iloc[0]

    # Fix invalid geometries if any (common OSM trick)
    if not polygon.is_valid:
        polygon = polygon.buffer(0)

    return polygon


def get_neighborhoods(polygon):
    """
    Download OSM neighborhoods inside the city polygon.
    Tries multiple tag combinations as neighborhoods may be tagged differently.

    - Input polygon is in EPSG:4326 (lat/lon).
    - We project to EPSG:3857 AFTER download to compute areas.
    """
    # Try multiple tag combinations for neighborhoods
    tag_combinations = [
        {"boundary": "neighbourhood"},
        {"place": "neighbourhood"},
        {"boundary": "administrative", "admin_level": "9"},  # Neighborhood level
        {"boundary": "administrative", "admin_level": "10"},  # Sub-neighborhood level
    ]
    
    all_neighborhoods = []
    
    for tags in tag_combinations:
        try:
            print(f"Trying tags: {tags}")
            neigh = ox.features_from_polygon(polygon, tags)
            
            if len(neigh) > 0:
                print(f"Found {len(neigh)} features with tags: {tags}")
                all_neighborhoods.append(neigh)
        except Exception as e:
            # OSMnx raises InsufficientResponseError when no features are found
            # Catch all exceptions and continue to next tag combination
            error_type = type(e).__name__
            print(f"No features found for tags {tags}: {error_type}")
            continue
    
    # If we found neighborhoods from any tag combination, combine them
    if all_neighborhoods:
        # Ensure all GeoDataFrames have the same CRS
        base_crs = all_neighborhoods[0].crs
        for i, gdf in enumerate(all_neighborhoods):
            if gdf.crs != base_crs:
                all_neighborhoods[i] = gdf.to_crs(base_crs)
        
        # Combine all GeoDataFrames
        neigh = gpd.GeoDataFrame(
            pd.concat(all_neighborhoods, ignore_index=True),
            crs=base_crs
        )
        # Remove duplicates based on geometry
        neigh = neigh.drop_duplicates(subset=["geometry"], keep="first")
    else:
        # Fallback: Create a grid-based division of the city
        print("No neighborhoods found in OSM. Creating grid-based neighborhoods...")
        neigh = create_grid_neighborhoods(polygon)
        return neigh
    
    # Keep only polygonal geometries
    neigh = neigh[neigh.geometry.type.isin(["Polygon", "MultiPolygon"])].copy()
    
    if len(neigh) == 0:
        print("No polygonal neighborhoods found. Creating grid-based neighborhoods...")
        neigh = create_grid_neighborhoods(polygon)
        return neigh

    # Project to meters for area calculation
    neigh = neigh.to_crs(epsg=3857)

    # Try to get name from various possible columns
    name_columns = ["name", "name:en", "place_name", "addr:city"]
    name_col = None
    for col in name_columns:
        if col in neigh.columns:
            name_col = col
            break
    
    if name_col:
        neigh = neigh.reset_index().rename(columns={name_col: "neighborhood_name"})
    else:
        neigh = neigh.reset_index()
        if "neighborhood_name" not in neigh.columns:
            neigh["neighborhood_name"] = None
    
    # Select relevant columns
    cols_to_keep = ["neighborhood_name", "geometry"]
    available_cols = [col for col in cols_to_keep if col in neigh.columns]
    neigh = neigh[available_cols]
    
    # Drop rows without names, or assign default names
    if "neighborhood_name" in neigh.columns:
        neigh = neigh.dropna(subset=["neighborhood_name"])
        if len(neigh) == 0:
            # If all were dropped, create grid-based neighborhoods
            print("No neighborhoods with names found. Creating grid-based neighborhoods...")
            neigh = create_grid_neighborhoods(polygon)
            return neigh
    else:
        # No name column, create grid-based neighborhoods
        print("No name column found. Creating grid-based neighborhoods...")
        neigh = create_grid_neighborhoods(polygon)
        return neigh

    neigh["area_km2"] = neigh.geometry.area / 1e6  # m² -> km²
    neigh["city"] = "Vancouver"

    return neigh


def create_grid_neighborhoods(polygon):
    """
    Create a grid-based neighborhood division as a fallback when OSM data is unavailable.
    Divides the city polygon into a 6x6 grid of neighborhoods.
    """
    
    # Get bounding box of the polygon
    bounds = polygon.bounds  # minx, miny, maxx, maxy
    
    # Project to metric CRS for grid creation
    polygon_gdf = gpd.GeoDataFrame([1], geometry=[polygon], crs="EPSG:4326")
    polygon_projected = polygon_gdf.to_crs(epsg=3857)
    polygon_geom = polygon_projected.geometry.iloc[0]
    bounds_proj = polygon_geom.bounds
    
    # Create a 6x6 grid
    n_rows, n_cols = 6, 6
    minx, miny, maxx, maxy = bounds_proj
    
    cell_width = (maxx - minx) / n_cols
    cell_height = (maxy - miny) / n_rows
    
    neighborhoods = []
    
    for i in range(n_rows):
        for j in range(n_cols):
            cell_minx = minx + j * cell_width
            cell_maxx = minx + (j + 1) * cell_width
            cell_miny = miny + i * cell_height
            cell_maxy = miny + (i + 1) * cell_height
            
            cell = box(cell_minx, cell_miny, cell_maxx, cell_maxy)
            
            # Intersect with city polygon
            intersection = cell.intersection(polygon_geom)
            
            # Only keep if intersection has area
            if intersection.area > 0:
                neighborhoods.append({
                    "neighborhood_name": f"Grid_{i+1}_{j+1}",
                    "geometry": intersection,
                    "area_km2": intersection.area / 1e6,
                    "city": "Vancouver"
                })
    
    neigh = gpd.GeoDataFrame(neighborhoods, crs="EPSG:3857")
    return neigh


def get_pois(polygon):
    """
    Download key amenities: schools, transit, malls, parks, hospitals.

    - Input polygon is EPSG:4326.
    - We project to EPSG:3857 AFTER we download.
    """
    tags = {
        "amenity": [
            "school", "college", "university",
            "bus_station", "hospital",
        ],
        "shop": ["mall", "supermarket"],
        "leisure": ["park"],
    }

    pois = ox.features_from_polygon(polygon, tags)

    # Project to metric CRS for any distance/area if needed later
    pois = pois.to_crs(epsg=3857)

    pois = pois[pois.geometry.type.isin(
        ["Point", "MultiPoint", "Polygon", "MultiPolygon"]
    )].copy()

    def classify(row):
        amenity = row.get("amenity", None)
        shop = row.get("shop", None)
        leisure = row.get("leisure", None)

        if amenity in ["school", "college", "university"]:
            return "school"
        if amenity == "bus_station":
            return "transit"
        if amenity == "hospital":
            return "hospital"
        if shop in ["mall", "supermarket"]:
            return "mall"
        if leisure == "park":
            return "park"
        return "other"

    pois["category"] = pois.apply(classify, axis=1)
    pois["city"] = "Vancouver"

    return pois


def main():
    os.makedirs(DATA_PROCESSED, exist_ok=True)

    # Get boundary in WGS84, fixed if invalid
    polygon = get_city_boundary()

    neighborhoods = get_neighborhoods(polygon)
    neighborhoods.to_file(
        os.path.join(DATA_PROCESSED, "neighborhoods.geojson"),
        driver="GeoJSON",
    )

    pois = get_pois(polygon)
    pois.to_file(
        os.path.join(DATA_PROCESSED, "pois.geojson"),
        driver="GeoJSON",
    )

    print("Saved data/processed/neighborhoods.geojson and pois.geojson")


if __name__ == "__main__":
    main()
