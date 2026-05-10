# Carbon Footprint of Municipal Organic Waste Systems (Carbon-MOWS)

Prospective life cycle assessment (LCA) framework for organic waste management in Montreal, integrating IAM-based scenario projections (SSP1–5) with a 3×3 technology matrix and a Streamlit dashboard.

## Overview

The framework links five Shared Socioeconomic Pathways (SSPs) to ecoinvent background databases updated by [premise](https://github.com/polca/premise) using REMIND and MESSAGE IAM outputs. LCA results feed a technology matrix (Scale × Technology Level) that serves as initial conditions for a future system dynamics model.

**SSP → IAM mapping**

| SSP  | Model   | Pathway        |
|------|---------|----------------|
| SSP1 | REMIND  | SSP1-PkBudg650 |
| SSP2 | REMIND  | SSP2-NDC       |
| SSP3 | REMIND  | SSP3-rollBack  |
| SSP4 | MESSAGE | SSP4-LO        |
| SSP5 | MESSAGE | SSP5-H         |

## Repository Structure

```
Carbon-Mows/
├── lca/                  # Python LCA package (tech matrix, Brightway runner, scipy matrix solver)
├── prospective/          # premise database generation script + exported sparse matrices
├── dashboard/            # Streamlit dashboard (SSP scenarios, year slider, GWP results)
├── estimation/           # Montreal waste estimation module (SSP population projections)
└── archive/              # Legacy material (old Shiny app, original Brightway notebooks)
```

## Environments

Two conda environments are required due to a bw2data version conflict:

| Environment | bw2data | Purpose |
|-------------|---------|---------|
| `premise`   | 4.x     | Generate prospective ecoinvent databases |
| `bw`        | 3.x     | Run LCA and Streamlit dashboard |

## Step 1 — Generate Prospective Databases

Run once (takes several hours for all SSPs × years):

```bash
conda activate premise
python prospective/generate_prospective_dbs.py
```

Edit `SSPS_TO_RUN` and `YEARS_TO_RUN` at the top of the script to control scope. Default: all 5 SSPs × {2030, 2050, 2080, 2100}.

Matrices are exported to `prospective/export/{model}/{pathway}/{year}/`.

## Step 2 — Run the Dashboard

```bash
conda activate bw
streamlit run dashboard/app.py
```

The dashboard shows GWP results (kg CO₂-eq / tonne OFMSW) for each SSP × year combination, using premise-generated prospective backgrounds where available and static ecoinvent 3.9.1 as fallback.

## Brightway Projects

| Project | Environment | Contents |
|---------|-------------|----------|
| `testproject7` | `bw` | OWM Facilities DB, ecoinvent 3.9.1-cutoff, IPCC 2021 methods |
| `carbon-mows-premise` | `premise` | ecoinvent 3.9.1-cutoff for premise |
