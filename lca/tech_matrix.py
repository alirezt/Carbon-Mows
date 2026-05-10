"""
Technology matrix: 3x3 (Scale x Technology Level) for Montreal organic waste management.
Defines facility mapping and SSP-specific initial proportions.
"""

SCALES = ["Domestic", "Local", "Centralized"]
LEVELS = ["Low", "Medium", "High"]

# ---------------------------------------------------------------------------
# Facility mapping for each matrix cell
# status: "existing" = in Carbon-Mows Brightway DB, "proxy" = future/hypothetical
# dataset: Brightway activity name to use for LCA
# ---------------------------------------------------------------------------
TECH_MATRIX = {
    "Domestic": {
        "Low":    {
            "facility": "Backyard composting",
            "status": "proxy",
            "dataset": "Composter_terrebonne",  # scaled proxy
            "scale_factor": 0.70,
        },
        "Medium": {
            "facility": "In-vessel home composter",
            "status": "proxy",
            "dataset": "Closed-tunnel Composter",
            "scale_factor": 0.70,
        },
        "High":   {
            "facility": "Home biodigester",
            "status": "proxy",
            "dataset": "AD",
            "scale_factor": 0.70,
        },
    },
    "Local": {
        "Low":    {
            "facility": "Community windrow composting",
            "status": "proxy",
            "dataset": "Composter_terrebonne",
            "scale_factor": 0.90,
        },
        "Medium": {
            "facility": "Small closed composter",
            "status": "proxy",
            "dataset": "Closed-tunnel Composter",
            "scale_factor": 0.90,
        },
        "High":   {
            "facility": "Small-scale anaerobic digestion",
            "status": "proxy",
            "dataset": "AD",
            "scale_factor": 0.90,
        },
    },
    "Centralized": {
        "Low":    {
            "facility": "Landfill with gas recovery (avg 6 HOC sites)",
            "status": "existing",
            "dataset": "Landfill_terrebonne",
            "scale_factor": 1.0,
            "dataset_group": [
                "Landfill_terrebonne",
                "Landfill_lachute",
                "Landfill_saint sophie",
                "Landfill_saint_thomas",
                "Landfill_cecile_de_milton",
                "Landfill_st-nicephore",
            ],
        },
        "Medium": {
            "facility": "Large windrow & closed composters (avg 5 sites)",
            "status": "existing",
            "dataset": "Composter_terrebonne",
            "scale_factor": 1.0,
            "dataset_group": [
                "Composter_terrebonne",
                "Composter_casselman",
                "Composter_complexe enviro st Michel",
                "Composter_saint thomas",
                "Closed-tunnel Composter",
            ],
        },
        "High":   {
            "facility": "Anaerobic digestion with biogas upgrading (avg 2 sites)",
            "status": "existing",
            "dataset": "AD",
            "scale_factor": 1.0,
            "dataset_group": [
                "AD",
                "NS_AD",
            ],
        },
    },
}

# ---------------------------------------------------------------------------
# SSP proportions — initial conditions (sum to 1.0 per scenario)
# Rationale:
#   SSP1: sustainability — decentralized, high-tech, landfill near zero
#   SSP2: middle road  — mostly centralized, gradual landfill reduction
#   SSP3: rivalry      — centralized, low-tech, high landfill
# ---------------------------------------------------------------------------
SSP_PROPORTIONS = {
    "SSP1": {
        "Domestic":    {"Low": 0.05, "Medium": 0.08, "High": 0.05},
        "Local":       {"Low": 0.06, "Medium": 0.10, "High": 0.08},
        "Centralized": {"Low": 0.05, "Medium": 0.33, "High": 0.20},
    },
    "SSP2": {
        "Domestic":    {"Low": 0.03, "Medium": 0.04, "High": 0.01},
        "Local":       {"Low": 0.05, "Medium": 0.07, "High": 0.03},
        "Centralized": {"Low": 0.18, "Medium": 0.42, "High": 0.17},
    },
    "SSP3": {
        "Domestic":    {"Low": 0.02, "Medium": 0.01, "High": 0.00},
        "Local":       {"Low": 0.04, "Medium": 0.02, "High": 0.00},
        "Centralized": {"Low": 0.38, "Medium": 0.38, "High": 0.15},
    },
    # SSP4: Inequality — elite access to high tech, majority uses low-tech centralized
    "SSP4": {
        "Domestic":    {"Low": 0.02, "Medium": 0.02, "High": 0.01},
        "Local":       {"Low": 0.04, "Medium": 0.05, "High": 0.02},
        "Centralized": {"Low": 0.28, "Medium": 0.38, "High": 0.18},
    },
    # SSP5: Fossil fuel development — high energy, centralized, high-tech but fossil-dependent
    "SSP5": {
        "Domestic":    {"Low": 0.02, "Medium": 0.02, "High": 0.02},
        "Local":       {"Low": 0.04, "Medium": 0.05, "High": 0.04},
        "Centralized": {"Low": 0.18, "Medium": 0.38, "High": 0.25},
    },
}

def get_matrix_df(ssp: str):
    """Return SSP proportions as a DataFrame (scales × levels)."""
    import pandas as pd
    props = SSP_PROPORTIONS[ssp]
    return pd.DataFrame(
        {level: [props[scale][level] for scale in SCALES] for level in LEVELS},
        index=SCALES,
    )

def validate_proportions():
    """Assert each SSP sums to 1.0."""
    for ssp, props in SSP_PROPORTIONS.items():
        total = sum(v for scale in props.values() for v in scale.values())
        assert abs(total - 1.0) < 1e-6, f"{ssp} proportions sum to {total}, not 1.0"

validate_proportions()
