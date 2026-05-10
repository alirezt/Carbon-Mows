"""
Montreal organic waste estimation.
Reads SSP population projections at ADA level and applies a per-capita waste rate.
"""

import pandas as pd
from pathlib import Path

# Path to the R model output CSV
POPULATION_CSV = Path(r"C:\My files\R projects\Ongoing\waste_ssp\output\montreal_ssp_population_by_ADA.csv")

# kg of organic waste per person per year (Montreal baseline ~2022)
# Source: Ville de Montréal open data — ~120 kg OFMSW/capita/yr
WASTE_RATE_KG_PER_CAPITA = 120.0

# SSPs available in the CSV
AVAILABLE_SSPS = ["SSP1", "SSP2", "SSP3", "SSP4", "SSP5"]


def load_population(ssps: list = None, interpolate_missing: bool = True) -> pd.DataFrame:
    """
    Load ADA-level population projections.
    Drops rows with NA population (outside Montreal agglomeration).
    Optionally interpolates missing SSP-year combinations (e.g. SSP1 2040).
    """
    df = pd.read_csv(POPULATION_CSV)
    df = df[df["pop_sum"].notna()].copy()
    df["year"] = df["year"].astype(int)

    if ssps:
        df = df[df["ssp"].isin(ssps)]

    if interpolate_missing:
        df = _interpolate_missing_years(df)

    return df


def estimate_waste(pop_df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply per-capita waste rate to population projections.
    Returns DataFrame with added columns: waste_kg, waste_tonnes.
    """
    df = pop_df.copy()
    df["waste_kg"]     = df["pop_sum"] * WASTE_RATE_KG_PER_CAPITA
    df["waste_tonnes"] = df["waste_kg"] / 1000.0
    df = df.rename(columns={"pop_sum": "population"})
    return df[["ssp", "year", "DGUID", "population", "waste_tonnes"]]


def city_totals(waste_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate ADA-level waste to city-level totals."""
    return (
        waste_df.groupby(["ssp", "year"])[["population", "waste_tonnes"]]
        .sum()
        .reset_index()
    )


def _interpolate_missing_years(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fill missing SSP-year combinations by linear interpolation per ADA.
    Known gaps: SSP1 2040, SSP1 2045, SSP1 2095, SSP3 2040.
    """
    all_years = sorted(df["year"].unique())
    all_ssps  = df["ssp"].unique()
    all_adas  = df["DGUID"].unique()

    full_index = pd.MultiIndex.from_product(
        [all_ssps, all_years, all_adas],
        names=["ssp", "year", "DGUID"],
    )
    df_full = (
        df.set_index(["ssp", "year", "DGUID"])
        .reindex(full_index)
        .reset_index()
    )
    df_full["pop_sum"] = (
        df_full.groupby(["ssp", "DGUID"])["pop_sum"]
        .transform(lambda s: s.interpolate(method="linear", limit_direction="both"))
    )
    return df_full[df_full["pop_sum"].notna()]
