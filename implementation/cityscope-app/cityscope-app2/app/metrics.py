# app/metrics.py

import pandas as pd


def min_max(series: pd.Series) -> pd.Series:
    min_v, max_v = series.min(), series.max()
    if max_v == min_v:
        return pd.Series(50, index=series.index)
    return 100 * (series - min_v) / (max_v - min_v)


def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()

    # Affordability: lower rent => higher score
    aff_raw = df["avg_rent"]
    df["affordability_score"] = 100 - min_max(aff_raw)

    df["transit_score"] = min_max(df["transit_per_km2"])
    df["schools_score"] = min_max(df["schools_per_km2"])
    df["amenities_score"] = min_max(df["amenities_per_km2"])

    # Weights for composite score
    w_afford, w_transit, w_school, w_amen = 0.4, 0.3, 0.2, 0.1

    df["composite_score"] = (
        w_afford * df["affordability_score"]
        + w_transit * df["transit_score"]
        + w_school * df["schools_score"]
        + w_amen * df["amenities_score"]
    )

    return df
