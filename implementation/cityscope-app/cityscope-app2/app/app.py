# app/app.py

import os

import folium
import geopandas as gpd
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_folium import st_folium

from metrics import compute_scores

DATA_PROCESSED = "data/processed"


@st.cache_data
def load_data():
    metrics_path = os.path.join(DATA_PROCESSED, "neighborhood_metrics.parquet")
    geo_path = os.path.join(DATA_PROCESSED, "neighborhoods_full.geojson")

    metrics = pd.read_parquet(metrics_path)
    metrics = compute_scores(metrics)

    gdf = gpd.read_file(geo_path)
    return metrics, gdf


def summary_section(metrics: pd.DataFrame):
    st.subheader("Summary")

    col1, col2, col3 = st.columns(3)
    col1.metric("Neighborhoods", len(metrics))
    col2.metric("Average rent (overall)", f"${metrics['avg_rent'].mean():.0f}")

    top = metrics.sort_values("composite_score", ascending=False).head(1)
    if not top.empty:
        col3.metric(
            "Top neighborhood",
            f"{top.iloc[0]['neighborhood_name']} ({top.iloc[0]['composite_score']:.1f})",
        )


def map_section(filtered_metrics: pd.DataFrame, full_gdf: gpd.GeoDataFrame):
    st.subheader("Neighborhood Map (Composite Score)")

    gdf_scores = full_gdf.merge(
        filtered_metrics[["neighborhood_name", "composite_score"]],
        on="neighborhood_name",
        how="inner",
    )

    gdf_scores_4326 = gdf_scores.to_crs(epsg=4326)

    center = gdf_scores_4326.geometry.centroid
    center_lat = center.y.mean()
    center_lon = center.x.mean()

    m = folium.Map(location=[center_lat, center_lon], zoom_start=12)

    folium.Choropleth(
        geo_data=gdf_scores_4326,
        data=gdf_scores_4326,
        columns=["neighborhood_name", "composite_score"],
        key_on="feature.properties.neighborhood_name",
        fill_opacity=0.7,
        line_opacity=0.2,
        legend_name="Composite Score",
    ).add_to(m)

    folium.GeoJson(
        gdf_scores_4326,
        tooltip=folium.features.GeoJsonTooltip(
            fields=["neighborhood_name", "composite_score"],
            aliases=["Neighborhood:", "Composite score:"],
            localize=True,
        ),
    ).add_to(m)

    st_folium(m, width=900, height=500)


def top_neighborhoods_section(filtered: pd.DataFrame):
    st.subheader("Top Neighborhoods by Composite Score")

    top10 = filtered.sort_values("composite_score", ascending=False).head(10)
    fig = px.bar(
        top10,
        x="neighborhood_name",
        y="composite_score",
        hover_data=["avg_rent", "transit_score", "schools_score", "amenities_score"],
    )
    fig.update_layout(xaxis_title="", yaxis_title="Composite score")
    st.plotly_chart(fig, use_container_width=True)


def tradeoff_section(filtered: pd.DataFrame):
    st.subheader("Rent vs Transit Density (Tradeoff)")

    fig = px.scatter(
        filtered,
        x="avg_rent",
        y="transit_per_km2",
        color="composite_score",
        hover_name="neighborhood_name",
        labels={
            "avg_rent": "Average rent ($)",
            "transit_per_km2": "Transit stops per km²",
        },
    )
    st.plotly_chart(fig, use_container_width=True)


def neighborhood_comparison_section(metrics: pd.DataFrame):
    st.subheader("Neighborhood Comparison (Side by Side)")

    cities = (
        ["All"] + sorted(metrics["city"].dropna().unique())
        if "city" in metrics.columns
        else ["All"]
    )
    selected_city = st.selectbox("Filter by city", options=cities, index=0)

    if selected_city != "All" and "city" in metrics.columns:
        df_city = metrics[metrics["city"] == selected_city].copy()
    else:
        df_city = metrics.copy()

    options = sorted(df_city["neighborhood_name"].unique())

    col_sel1, col_sel2 = st.columns(2)
    with col_sel1:
        nbhd1 = st.selectbox("Neighborhood A", options=options, key="nbhd1")
    with col_sel2:
        nbhd2 = st.selectbox("Neighborhood B", options=options, key="nbhd2")

    if nbhd1 == nbhd2:
        st.info("Select two different neighborhoods to compare.")
        return

    data1 = df_city[df_city["neighborhood_name"] == nbhd1].iloc[0]
    data2 = df_city[df_city["neighborhood_name"] == nbhd2].iloc[0]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"### {nbhd1}")
        st.metric("Average rent", f"${data1['avg_rent']:.0f}")
        st.metric("Composite score", f"{data1['composite_score']:.1f}")
        st.metric("Transit score", f"{data1['transit_score']:.1f}")
        st.metric("Schools score", f"{data1['schools_score']:.1f}")
        st.metric("Amenities score", f"{data1['amenities_score']:.1f}")

    with c2:
        st.markdown(f"### {nbhd2}")
        st.metric("Average rent", f"${data2['avg_rent']:.0f}")
        st.metric("Composite score", f"{data2['composite_score']:.1f}")
        st.metric("Transit score", f"{data2['transit_score']:.1f}")
        st.metric("Schools score", f"{data2['schools_score']:.1f}")
        st.metric("Amenities score", f"{data2['amenities_score']:.1f}")

    st.markdown("#### Profile comparison")

    dims = ["affordability_score", "transit_score", "schools_score", "amenities_score"]
    labels = ["Affordability", "Transit", "Schools", "Amenities"]

    vals1 = [data1[d] for d in dims]
    vals2 = [data2[d] for d in dims]

    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(r=vals1, theta=labels, fill="toself", name=nbhd1)
    )
    fig.add_trace(
        go.Scatterpolar(r=vals2, theta=labels, fill="toself", name=nbhd2)
    )
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("#### Detailed metrics table")
    comp_df = (
        df_city[df_city["neighborhood_name"].isin([nbhd1, nbhd2])]
        [
            [
                "neighborhood_name",
                "avg_rent",
                "affordability_score",
                "transit_score",
                "schools_score",
                "amenities_score",
                "composite_score",
            ]
        ]
        .set_index("neighborhood_name")
    )
    st.dataframe(comp_df)


def main():
    st.set_page_config(page_title="CityScope", layout="wide")
    st.title("CityScope: Real Estate & Community Data Explorer (BC – Neighborhoods)")

    metrics, gdf = load_data()

    # Sidebar filters
    st.sidebar.header("Filters")
    
    # Handle rent filter - if all neighborhoods have the same rent, create a range
    rent_min = metrics["avg_rent"].min()
    rent_max = metrics["avg_rent"].max()
    
    if rent_min == rent_max:
        # All neighborhoods have the same rent - create a range around it
        # Use ±20% or minimum $500 range, whichever is larger
        rent_value = rent_min
        range_amount = max(rent_value * 0.2, 500)
        slider_min = max(0, int(rent_value - range_amount))
        slider_max = int(rent_value + range_amount)
        default_value = int(rent_value)
        st.sidebar.info(f"All neighborhoods have the same rent: ${rent_value:.0f}")
    else:
        slider_min = int(rent_min)
        slider_max = int(rent_max)
        default_value = int(rent_max)
    
    max_rent = st.sidebar.slider(
        "Max average rent ($)",
        slider_min,
        slider_max,
        default_value,
    )
    min_score = st.sidebar.slider("Minimum composite score", 0, 100, 0)

    filtered = metrics[
        (metrics["avg_rent"] <= max_rent)
        & (metrics["composite_score"] >= min_score)
    ].copy()

    summary_section(metrics)
    map_section(filtered, gdf)
    top_neighborhoods_section(filtered)
    tradeoff_section(filtered)
    neighborhood_comparison_section(metrics)


if __name__ == "__main__":
    main()
