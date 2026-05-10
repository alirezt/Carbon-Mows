"""
LCA calculations for the Carbon-Mows technology matrix.

For each matrix cell × SSP × year:
  1. Check if premise-exported sparse matrices exist for this SSP/year
  2. Run LCA for each facility dataset (average for grouped cells)
  3. Apply scale_factor for proxy (future/hypothetical) cells
  4. Weight by SSP proportions → aggregate city-level GWP
"""

import warnings
import brightway2 as bw
import pandas as pd
import numpy as np

from lca.tech_matrix import TECH_MATRIX, SSP_PROPORTIONS, SCALES, LEVELS

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

BW_PROJECT = "testproject7"
OWM_DB     = "OWM Facilities"
STATIC_DB  = "ecoinvent-3.9.1-cutoff"

IPCC_METHOD = ('IPCC 2021', 'climate change', 'global warming potential (GWP100)')

# Maps each SSP to the IAM model + pathway used by premise.
SSP_TO_PREMISE = {
    "SSP1": {"model": "remind",  "pathway": "SSP1-PkBudg650"},  # 1.5°C, strong action
    "SSP2": {"model": "remind",  "pathway": "SSP2-NDC"},         # Current pledges
    "SSP3": {"model": "remind",  "pathway": "SSP3-rollBack"},    # Rollback scenario
    "SSP4": {"model": "message", "pathway": "SSP4-LO"},          # Inequality, low overshoot
    "SSP5": {"model": "message", "pathway": "SSP5-H"},           # Fossil fuel development
}

ALL_SSPS = list(SSP_TO_PREMISE.keys())
ALL_YEARS = list(range(2025, 2105, 5))  # 2025–2100 in 5-year steps

# ---------------------------------------------------------------------------
# Brightway helpers
# ---------------------------------------------------------------------------

def _activate_project():
    bw.projects.set_current(BW_PROJECT)


def _get_ipcc_method():
    _activate_project()
    if IPCC_METHOD not in bw.methods:
        raise RuntimeError(
            f"Method {IPCC_METHOD} not found in project '{BW_PROJECT}'. "
            f"Available families: {sorted(set(m[0] for m in bw.methods))[:5]}"
        )
    return IPCC_METHOD


def _premise_cfg(ssp: str) -> dict:
    return SSP_TO_PREMISE[ssp]


def _use_matrices(ssp: str, year: int) -> bool:
    """Check if premise-exported matrices exist for this SSP/year."""
    from lca.matrix_lca import matrices_exist
    cfg = _premise_cfg(ssp)
    return matrices_exist(cfg["model"], cfg["pathway"], year)


def _lca_score(activity, method) -> float:
    lca = bw.LCA({activity: 1}, method)
    lca.lci()
    lca.lcia()
    return lca.score


def _get_activity(db_owm: bw.Database, dataset_name: str):
    """Look up an OWM Facilities activity by name."""
    matches = [a for a in db_owm if dataset_name.lower() in a["name"].lower()]
    if not matches:
        raise KeyError(f"Dataset '{dataset_name}' not found in '{OWM_DB}'.")
    return matches[0]


# ---------------------------------------------------------------------------
# Core LCA per cell
# ---------------------------------------------------------------------------

def lca_cell(scale: str, level: str, ssp: str, year: int, method=None) -> float:
    """
    GWP (kg CO2-eq / tonne OFMSW) for one matrix cell under a given SSP/year.

    Tries premise-exported matrices first; OWM foreground activities fall back
    to Brightway with static ecoinvent background.
    """
    cell     = TECH_MATRIX[scale][level]
    factor   = cell.get("scale_factor", 1.0)
    datasets = cell.get("dataset_group", [cell["dataset"]])

    if method is None:
        method = _get_ipcc_method()
    _activate_project()
    db_owm = bw.Database(OWM_DB)

    use_matrices = _use_matrices(ssp, year)
    if use_matrices:
        from lca.matrix_lca import lca_score_matrix
        cfg = _premise_cfg(ssp)

    scores = []
    for name in datasets:
        score = None
        if use_matrices:
            try:
                score = lca_score_matrix(name, cfg["model"], cfg["pathway"], year)
            except KeyError:
                pass  # foreground activity not in ecoinvent matrices — fall through
            except Exception as e:
                warnings.warn(f"Matrix LCA failed for '{name}': {e}", UserWarning)
        if score is None:
            try:
                act   = _get_activity(db_owm, name)
                score = _lca_score(act, method)
            except Exception as e:
                warnings.warn(f"LCA failed for '{name}': {e}", UserWarning)
        if score is not None:
            scores.append(score)

    if not scores:
        return np.nan
    return float(np.mean(scores)) * factor


# ---------------------------------------------------------------------------
# Full matrix run
# ---------------------------------------------------------------------------

def run_matrix_lca(ssp: str, year: int) -> pd.DataFrame:
    """
    Run LCA for all 9 cells of the technology matrix.

    Returns a DataFrame with columns:
        scale, level, gwp, proportion, gwp_weighted, database, prospective
    """
    using_matrices = _use_matrices(ssp, year)
    cfg            = _premise_cfg(ssp)
    db_name        = f"{cfg['model']}_{cfg['pathway']}_{year} (matrices)" if using_matrices else STATIC_DB
    method         = None if using_matrices else _get_ipcc_method()

    rows = []
    for scale in SCALES:
        for level in LEVELS:
            prop = SSP_PROPORTIONS[ssp][scale][level]
            gwp  = lca_cell(scale, level, ssp, year, method=method)
            rows.append({
                "scale":        scale,
                "level":        level,
                "gwp":          gwp,
                "proportion":   prop,
                "gwp_weighted": gwp * prop if not np.isnan(gwp) else np.nan,
                "database":     db_name,
                "prospective":  using_matrices,
            })

    return pd.DataFrame(rows)


def aggregate_gwp(matrix_df: pd.DataFrame) -> float:
    """Weighted average GWP across all cells (kg CO2-eq / tonne OFMSW)."""
    return matrix_df["gwp_weighted"].sum()


# ---------------------------------------------------------------------------
# Multi-SSP / multi-year convenience
# ---------------------------------------------------------------------------

def run_all(
    ssps: list = None,
    years: list = None,
) -> pd.DataFrame:
    """Run the full matrix for all SSP × year combinations."""
    if ssps is None:
        ssps = ALL_SSPS
    if years is None:
        years = ALL_YEARS
    results = []
    for ssp in ssps:
        for year in years:
            df = run_matrix_lca(ssp, year)
            df["ssp"]  = ssp
            df["year"] = year
            results.append(df)
    return pd.concat(results, ignore_index=True)


def aggregate_summary(ssps=None, years=None) -> pd.DataFrame:
    """Aggregate GWP table: rows = years, columns = SSPs."""
    if ssps is None:
        ssps = ALL_SSPS
    if years is None:
        years = ALL_YEARS
    all_df = run_all(ssps, years)
    return (
        all_df.groupby(["ssp", "year"])["gwp_weighted"]
        .sum()
        .reset_index()
        .pivot(index="year", columns="ssp", values="gwp_weighted")
    )
