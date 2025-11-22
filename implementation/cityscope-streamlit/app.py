import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk

# --------- PAGE CONFIG & BASIC STYLING ----------
st.set_page_config(
    page_title="CityScope – Neighbourhood Explorer",
    page_icon="📍",
    layout="wide"
)

st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    .big-title {
        font-size: 2.0rem;
        font-weight: 700;
        margin-bottom: 0.25rem;
    }
    .subtitle {
        font-size: 0.95rem;
        color: #6b7280;
        margin-bottom: 1rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------- LOAD DATA ----------
@st.cache_data
def load_data():
    neigh_df = pd.read_csv("data/neighbourhoods.csv")
    rent_df = pd.read_csv("data/rents.csv")

    # Aggregated amenity counts per neighbourhood
    try:
        poi_counts_df = pd.read_csv("data/poi_counts.csv")
    except FileNotFoundError:
        poi_counts_df = pd.DataFrame({
            "neighbourhood_id": neigh_df["neighbourhood_id"],
            "schools": 0,
            "restaurants": 0,
            "transit_stops": 0,
            "parks": 0,
            "grocery": 0,
        })

    # Individual OSM POI points
    try:
        poi_points_df = pd.read_csv("data/osm_pois.csv")
    except FileNotFoundError:
        poi_points_df = pd.DataFrame(
            columns=["neighbourhood_id", "category", "name", "lat", "lon"]
        )

    return neigh_df, rent_df, poi_counts_df, poi_points_df


neigh_df, rent_df, poi_counts_df, poi_points_df = load_data()
neigh_df = neigh_df.merge(poi_counts_df, on="neighbourhood_id", how="left")

# Safety checks
required_neigh_cols = {"neighbourhood_id", "name", "lat", "lon", "population"}
missing = required_neigh_cols - set(neigh_df.columns)
if missing:
    st.error(f"Missing columns in neighbourhoods.csv: {missing}")
    st.stop()

required_rent_cols = {"neighbourhood_id", "year", "bed_type", "avg_rent"}
missing_r = required_rent_cols - set(rent_df.columns)
if missing_r:
    st.error(f"Missing columns in rents.csv: {missing_r}")
    st.stop()

# --------- SCORE CALCULATION ----------
def compute_scores(neigh_df: pd.DataFrame, rent_df: pd.DataFrame, bed_type: str, year: int) -> pd.DataFrame:
    """
    Score is based ONLY on:
    - avg_rent (affordability)
    - population (size)
    - transit_stops (transit access)
    - amenities counts: schools, restaurants, parks, grocery
    """
    rent_year = (
        rent_df[(rent_df["bed_type"] == bed_type) & (rent_df["year"] == year)]
        .groupby("neighbourhood_id", as_index=False)["avg_rent"]
        .mean()
    )

    df = neigh_df.merge(rent_year, on="neighbourhood_id", how="left")

    # Handle missing rent by filling with median
    df["avg_rent"] = df["avg_rent"].fillna(df["avg_rent"].median())

    # 1) Rent score (lower rent = better)
    r_min, r_max = df["avg_rent"].min(), df["avg_rent"].max()
    df["rent_score"] = 1 - (df["avg_rent"] - r_min) / (r_max - r_min + 1e-9)

    # 2) Size score from population (bigger = more options)
    p_min, p_max = df["population"].min(), df["population"].max()
    if p_max - p_min < 1e-9:
        df["size_score"] = 0.5
    else:
        df["size_score"] = (df["population"] - p_min) / (p_max - p_min + 1e-9)

    # 3) Transit score from transit_stops count
    if "transit_stops" in df.columns:
        t_min, t_max = df["transit_stops"].min(), df["transit_stops"].max()
        if t_max - t_min < 1e-9:
            df["transit_score"] = 0.5
        else:
            df["transit_score"] = (df["transit_stops"] - t_min) / (t_max - t_min + 1e-9)
    else:
        df["transit_score"] = 0.5

    # 4) Amenities score from schools + restaurants + parks + grocery
    amenity_cols = [c for c in ["schools", "restaurants", "parks", "grocery"] if c in df.columns]
    if amenity_cols:
        norm_cols = []
        for col in amenity_cols:
            c_min, c_max = df[col].min(), df[col].max()
            norm_col = f"{col}_norm"
            if c_max - c_min < 1e-9:
                df[norm_col] = 0.5
            else:
                df[norm_col] = (df[col] - c_min) / (c_max - c_min + 1e-9)
            norm_cols.append(norm_col)

        df["amenities_score"] = df[norm_cols].mean(axis=1)
    else:
        df["amenities_score"] = 0.5

    return df


def apply_weights(
    df: pd.DataFrame,
    w_rent: float,
    w_transit: float,
    w_amenities: float,
    w_size: float,
) -> pd.DataFrame:
    num = (
        w_rent      * df["rent_score"] +
        w_transit   * df["transit_score"] +
        w_amenities * df["amenities_score"] +
        w_size      * df["size_score"]
    )
    denom = w_rent + w_transit + w_amenities + w_size + 1e-9
    df["total_score"] = num / denom
    return df

# --------- SIMPLE "LLM-LIKE" INTERPRETER ----------
def interpret_requirements(text: str) -> dict:
    """
    Very simple keyword-based "intent" detection.
    You can later replace this with a real LLM call.
    """
    t = text.lower()
    intents = {
        "budget": any(w in t for w in ["cheap", "affordable", "budget", "low rent", "expensive"]),
        "family": any(w in t for w in ["family", "kids", "children", "school"]),
        "student": any(w in t for w in ["student", "university", "college"]),
        "transit": any(w in t for w in ["transit", "skytrain", "bus", "no car", "car-free", "walkable", "walk"]),
        "restaurants": any(w in t for w in ["restaurant", "restaurants", "food", "cafe", "coffee", "nightlife", "bar"]),
        "parks": any(w in t for w in ["park", "green", "nature", "outdoor"]),
        "quiet": any(w in t for w in ["quiet", "calm", "peaceful", "not busy", "less crowded"]),
    }
    return intents


def recommend_neighbourhoods(df: pd.DataFrame, user_text: str, top_n: int = 5):
    intents = interpret_requirements(user_text)
    rec_df = df.copy()

    # Start from total_score and gently push based on intents
    score = rec_df["total_score"].copy()

    if intents["budget"]:
        # prioritize affordability
        score += rec_df["rent_score"] * 0.4

    if intents["family"]:
        # prioritize amenities and size (schools, parks, etc.)
        score += rec_df["amenities_score"] * 0.3
        score += rec_df["size_score"] * 0.2

    if intents["student"]:
        # similar to budget + transit + restaurants
        score += rec_df["rent_score"] * 0.3
        score += rec_df["transit_score"] * 0.3
        score += rec_df["amenities_score"] * 0.2

    if intents["transit"]:
        score += rec_df["transit_score"] * 0.4

    if intents["restaurants"]:
        # we don't have restaurant-specific score, but amenities_score correlates
        score += rec_df["amenities_score"] * 0.3

    if intents["parks"]:
        score += rec_df["amenities_score"] * 0.2

    if intents["quiet"]:
        # penalize very large/populous neighbourhoods a bit
        score -= rec_df["size_score"] * 0.2

    rec_df["ai_score"] = score

    # Rank
    rec_df = rec_df.sort_values("ai_score", ascending=False).head(top_n)

    # Build a simple explanation
    reasons = []
    if intents["budget"]:
        reasons.append("• I prioritized **cheaper rent**.")
    if intents["family"]:
        reasons.append("• I boosted areas with **more amenities and larger neighbourhood size** (better for families).")
    if intents["student"]:
        reasons.append("• I focused on **affordability**, **transit access**, and **amenities** for a student lifestyle.")
    if intents["transit"]:
        reasons.append("• I preferred neighbourhoods with **more transit stops**.")
    if intents["restaurants"]:
        reasons.append("• I preferred neighbourhoods with **richer amenity density** (restaurants, cafes, etc.).")
    if intents["parks"]:
        reasons.append("• I slightly favoured neighbourhoods that are **richer in amenities**, including parks.")
    if intents["quiet"]:
        reasons.append("• I slightly down-ranked the **most dense / busy** neighbourhoods to keep things quieter.")

    if not reasons:
        reasons.append("• I used your current weights and overall score to find the best matches.")

    explanation = "Based on your description, here's how I interpreted your needs:\n\n" + "\n".join(reasons)

    return rec_df, explanation

# --------- SIDEBAR FILTERS ----------
st.sidebar.title("Filters & Preferences")

bed_type = st.sidebar.selectbox("Bedroom type", sorted(rent_df["bed_type"].unique()))
year = st.sidebar.selectbox("Year", sorted(rent_df["year"].unique()))

st.sidebar.markdown("**Score Weights (all based on real counts)**")
w_rent      = st.sidebar.slider("Affordability (rent)",   0.0, 1.0, 0.30, 0.05)
w_transit   = st.sidebar.slider("Transit access",         0.0, 1.0, 0.25, 0.05)
w_amenities = st.sidebar.slider("Amenities (OSM)",        0.0, 1.0, 0.25, 0.05)
w_size      = st.sidebar.slider("Neighbourhood size",     0.0, 1.0, 0.20, 0.05)

st.sidebar.markdown("---")
max_rent_default = float(rent_df["avg_rent"].quantile(0.75))
max_rent_filter = st.sidebar.number_input(
    "Max monthly rent ($)", value=max_rent_default, min_value=0.0, step=100.0
)

min_pop_filter = st.sidebar.number_input(
    "Min population (size filter)", value=0, min_value=0, step=5000
)
min_transit_filter = st.sidebar.number_input(
    "Min # transit stops", value=0, min_value=0, step=5
)
min_amenities_filter = st.sidebar.number_input(
    "Min total amenities (schools+restaurants+parks+grocery)", value=0, min_value=0, step=10
)

min_score_filter = st.sidebar.slider("Minimum total score", 0.0, 1.0, 0.0, 0.05)

city_col = "city" if "city" in neigh_df.columns else None
if city_col:
    st.sidebar.markdown("---")
    cities = ["All"] + sorted(neigh_df[city_col].dropna().unique().tolist())
    selected_city = st.sidebar.selectbox("City / Region", cities)
else:
    selected_city = "All"

st.sidebar.markdown("---")
st.sidebar.markdown("**Show on map**")
show_schools     = st.sidebar.checkbox("Schools", True)
show_restaurants = st.sidebar.checkbox("Restaurants", False)
show_transit     = st.sidebar.checkbox("Transit stops", False)
show_parks       = st.sidebar.checkbox("Parks", False)
show_grocery     = st.sidebar.checkbox("Grocery / Markets", False)

# --------- COMPUTE SCORES & FILTER ----------
score_df = compute_scores(neigh_df, rent_df, bed_type, year)
score_df = apply_weights(score_df, w_rent, w_transit, w_amenities, w_size)

score_df["total_amenities"] = score_df[["schools", "restaurants", "parks", "grocery"]].sum(axis=1)

mask = (
    (score_df["avg_rent"] <= max_rent_filter) &
    (score_df["population"] >= min_pop_filter) &
    (score_df["transit_stops"] >= min_transit_filter) &
    (score_df["total_amenities"] >= min_amenities_filter) &
    (score_df["total_score"] >= min_score_filter)
)
if selected_city != "All" and city_col:
    mask &= (score_df[city_col] == selected_city)

filtered_df = score_df[mask].copy()

if filtered_df.empty:
    st.warning("No neighbourhoods match your filters. Try relaxing them.")
    st.stop()

# Filter OSM POIs to only the visible neighbourhoods
visible_neighbourhood_ids = set(filtered_df["neighbourhood_id"])
poi_points_visible = poi_points_df[poi_points_df["neighbourhood_id"].isin(visible_neighbourhood_ids)].copy()

# --------- PAGE HEADER ----------
st.markdown('<div class="big-title">CityScope – Neighbourhood Explorer</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">Score and compare neighbourhoods using rent, size, transit, and real amenities from OpenStreetMap.</div>',
    unsafe_allow_html=True,
)

# --------- TABS ----------
tab_explore, tab_ai = st.tabs(["🗺 Explore map", "🤖 AI assistant"])

# ============================================================
# TAB 1: EXPLORE MAP (your existing UI)
# ============================================================
with tab_explore:
    center_lat = filtered_df["lat"].mean()
    center_lon = filtered_df["lon"].mean()

    def score_to_rgb(score: float):
        if score <= 0.5:
            ratio = score / 0.5
            r = 255
            g = int(255 * ratio)
            b = 0
        else:
            ratio = (score - 0.5) / 0.5
            r = int(255 * (1 - ratio))
            g = 255
            b = 0
        return [r, g, b]

    filtered_df["color"] = filtered_df["total_score"].apply(score_to_rgb)

    size_metric = filtered_df["population"]
    size_min, size_max = float(size_metric.min()), float(size_metric.max())
    if size_max - size_min < 1e-9:
        filtered_df["radius"] = 200
    else:
        filtered_df["radius"] = 200 + 800 * (size_metric - size_min) / (size_max - size_min + 1e-9)

    map_df = filtered_df[["name", "lat", "lon", "avg_rent", "total_score", "radius", "color"]].copy()
    map_df["tooltip_html"] = map_df.apply(
        lambda r: f"<b>{r['name']}</b><br/>Score: {r['total_score']:.2f}<br/>Avg rent: ${r['avg_rent']:.0f}",
        axis=1,
    )

    if not poi_points_visible.empty:
        poi_points_visible["name"] = poi_points_visible["name"].fillna("")
        poi_points_visible["tooltip_html"] = poi_points_visible.apply(
            lambda r: f"<b>{str(r['category']).replace('_', ' ').title()}</b><br/>{r['name'] or 'Amenity'}",
            axis=1,
        )

    map_col, info_col = st.columns([3, 2])

    with map_col:
        st.subheader("Interactive Neighbourhood Map")

        layers = []

        neighbourhood_layer = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position="[lon, lat]",
            get_radius="radius",
            get_fill_color="color",
            pickable=True,
            opacity=0.8,
        )
        layers.append(neighbourhood_layer)

        def poi_layer(category: str, color: list, radius: int):
            if poi_points_visible.empty:
                return None
            df_cat = poi_points_visible[poi_points_visible["category"] == category]
            if df_cat.empty:
                return None
            return pdk.Layer(
                "ScatterplotLayer",
                data=df_cat,
                get_position="[lon, lat]",
                get_radius=radius,
                get_fill_color=color,
                pickable=True,
                opacity=0.7,
            )

        if show_schools:
            layer = poi_layer("schools", [0, 100, 255], 60)
            if layer:
                layers.append(layer)

        if show_restaurants:
            layer = poi_layer("restaurants", [255, 99, 71], 50)
            if layer:
                layers.append(layer)

        if show_transit:
            layer = poi_layer("transit_stops", [0, 200, 150], 50)
            if layer:
                layers.append(layer)

        if show_parks:
            layer = poi_layer("parks", [50, 205, 50], 70)
            if layer:
                layers.append(layer)

        if show_grocery:
            layer = poi_layer("grocery", [255, 215, 0], 60)
            if layer:
                layers.append(layer)

        view_state = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=10,
            pitch=0,
        )

        tooltip = {
            "html": "{tooltip_html}",
            "style": {"backgroundColor": "rgba(15, 23, 42, 0.9)", "color": "white"}
        }

        deck = pdk.Deck(
            layers=layers,
            initial_view_state=view_state,
            tooltip=tooltip,
            map_style=None,
        )

        st.pydeck_chart(deck, use_container_width=True)

    with info_col:
        st.subheader("Ranked Neighbourhoods (objective score)")

        show_cols = [
            "name",
            "city" if "city" in filtered_df.columns else None,
            "avg_rent",
            "population",
            "transit_stops",
            "total_amenities",
            "total_score",
        ]
        show_cols = [c for c in show_cols if c is not None and c in filtered_df.columns]

        st.dataframe(
            filtered_df[show_cols]
            .sort_values("total_score", ascending=False)
            .reset_index(drop=True),
            use_container_width=True
        )

    st.markdown("---")
    st.subheader("Rent vs Score Overview")

    chart_df = filtered_df[["name", "avg_rent", "total_score"]].sort_values("avg_rent")
    st.bar_chart(chart_df, x="name", y="avg_rent")

    st.markdown("---")
    st.subheader("Compare neighbourhoods")

    selected_names = st.multiselect(
        "Select neighbourhoods to compare:",
        options=list(filtered_df["name"].unique()),
    )

    if selected_names:
        compare_df = filtered_df[filtered_df["name"].isin(selected_names)].copy()

        metrics_for_compare = [
            "avg_rent",
            "population",
            "transit_stops",
            "total_amenities",
            "rent_score",
            "transit_score",
            "amenities_score",
            "size_score",
            "total_score",
        ]
        metrics_for_compare = [m for m in compare_df.columns if m in metrics_for_compare]

        st.write("Raw metrics:")
        st.dataframe(compare_df[["name"] + metrics_for_compare].reset_index(drop=True))

        metric_to_plot = st.selectbox(
            "Pick a metric to visualize:",
            metrics_for_compare,
            index=metrics_for_compare.index("total_score") if "total_score" in metrics_for_compare else 0,
        )

        st.write(f"Comparison for **{metric_to_plot}**")
        plot_df = compare_df[["name", metric_to_plot]].set_index("name")
        st.bar_chart(plot_df)
    else:
        st.info("Select 2–5 neighbourhoods above to see a side-by-side comparison.")

# ============================================================
# TAB 2: AI ASSISTANT
# ============================================================
with tab_ai:
    st.subheader("Neighbourhood AI Assistant")
    st.write(
        "Describe what you're looking for and I'll suggest neighbourhoods based on "
        "rent, transit, amenities, and size."
    )

    example_prompt = (
        "Example: I'm a student with a low budget, I don't have a car, "
        "and I want good transit and lots of restaurants."
    )
    st.caption(example_prompt)

    user_query = st.text_area(
        "Your requirements",
        value="",
        placeholder="Tell me about your budget, lifestyle, commute, and what matters to you...",
        height=120,
    )

    if st.button("Get AI recommendations", type="primary"):
        if not user_query.strip():
            st.warning("Please type a short description of what you're looking for.")
        else:
            # Use the currently FILTERED dataset so it respects sidebar filters
            rec_df, explanation = recommend_neighbourhoods(filtered_df, user_query, top_n=5)

            st.markdown("### How I interpreted your needs")
            st.markdown(explanation)

            st.markdown("### Recommended neighbourhoods for you")
            rec_cols = [
                "name",
                "city" if "city" in rec_df.columns else None,
                "avg_rent",
                "population",
                "transit_stops",
                "total_amenities",
                "total_score",
                "ai_score",
            ]
            rec_cols = [c for c in rec_cols if c is not None and c in rec_df.columns]

            st.dataframe(
                rec_df[rec_cols].reset_index(drop=True),
                use_container_width=True
            )

            st.markdown(
                "_These suggestions are based purely on the data in the app and simple AI logic. "
                "You can refine them using the filters in the left sidebar._"
            )
    else:
        st.info("Describe your situation above and click **Get AI recommendations**.")
