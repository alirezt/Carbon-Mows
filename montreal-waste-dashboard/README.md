# Montreal Organic Waste Dashboard

Streamlit dashboard for exploring organic/food waste, population, land use, and
residential density by Montreal borough/municipality.

## Deploy on Streamlit Community Cloud

- Repository: this repo
- Branch: `montreal-dashboard-v1`
- Main file path: `montreal-waste-dashboard/app.py`

## Run locally

```
cd montreal-waste-dashboard
pip install -r requirements.txt
streamlit run app.py
```

## Data

All data in `data/` is pre-built from public sources (Données Québec, ISQ) —
no raw source shapefiles or scripts are included here. The full pipeline that
builds `data/cache/*.pkl` from source lives in the `montreal population`
project (not part of this repo).

Waste figures use only the public Données Québec bilan-massique series.
