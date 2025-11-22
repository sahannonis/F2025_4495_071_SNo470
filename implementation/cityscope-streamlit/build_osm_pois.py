import pandas as pd
import osmnx as ox

# Load neighbourhood centroids
neigh_df = pd.read_csv("data/neighbourhoods.csv")

# Radius around each neighbourhood centroid in meters
RADIUS_M = 1000  # 1 km radius – you can change this

# OSM tag groups for our categories
TAGS = {
    "schools": {
        "amenity": ["school", "college", "university"],
    },
    "restaurants": {
        "amenity": ["restaurant", "cafe", "fast_food"],
    },
    "transit_stops": {
        "highway": ["bus_stop"],
        # You can add more here, e.g. public_transport, railway, etc.
    },
    "parks": {
        "leisure": ["park"],
    },
    "grocery": {
        "shop": ["supermarket", "convenience", "greengrocer"],
    },
}

poi_rows = []    # one row per actual POI point
count_rows = []  # aggregated counts per neighbourhood

for _, nrow in neigh_df.iterrows():
    nid = nrow["neighbourhood_id"]
    lat = nrow["lat"]
    lon = nrow["lon"]

    print(f"=== Fetching POIs around {nid} ({lat}, {lon}) ===")

    counts = {"neighbourhood_id": nid}

    for category, tags in TAGS.items():
        try:
            # Get all features around the centroid within RADIUS_M
            gdf = ox.features_from_point(
                (lat, lon),
                tags=tags,
                dist=RADIUS_M,
            )
        except Exception as e:
            print(f"  [WARN] Error fetching {category} for {nid}: {e}")
            gdf = None

        if gdf is None or gdf.empty:
            counts[category] = 0
            continue

        counts[category] = len(gdf)

        # Convert each feature to a single point (geometry centroid if polygon)
        for _, row in gdf.iterrows():
            geom = row.get("geometry", None)
            if geom is None:
                continue

            try:
                # If it's a point, use it; otherwise use centroid
                point = geom.centroid if geom.geom_type != "Point" else geom
                poi_lat = point.y
                poi_lon = point.x
            except Exception:
                continue

            name = row.get("name", "")

            poi_rows.append(
                {
                    "neighbourhood_id": nid,
                    "category": category,
                    "name": name,
                    "lat": poi_lat,
                    "lon": poi_lon,
                }
            )

    count_rows.append(counts)

# Save aggregated counts
poi_counts_df = pd.DataFrame(count_rows)
poi_counts_df.to_csv("data/poi_counts.csv", index=False)
print("✅ Saved data/poi_counts.csv")

# Save full list of POI points
poi_points_df = pd.DataFrame(poi_rows)
poi_points_df.to_csv("data/osm_pois.csv", index=False)
print("✅ Saved data/osm_pois.csv")

