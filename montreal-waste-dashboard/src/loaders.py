import os
import pickle
import lzma
import pandas as pd
from src.constants import ADMIN_UNITS_PKL, POPULATION_CSV, CACHE_DIR


def load_admin_units():
    with open(ADMIN_UNITS_PKL, "rb") as f:
        units = pickle.load(f)
    for u in units:
        if not u["geom"].is_valid:
            u["geom"] = u["geom"].buffer(0)
    return units


def _load_pickle(name):
    with open(os.path.join(CACHE_DIR, name), "rb") as f:
        return pickle.load(f)


def load_parcels_by_unit():
    with lzma.open(os.path.join(CACHE_DIR, "parcels_by_unit.pkl.xz"), "rb") as f:
        return pickle.load(f)


def load_landuse_by_unit():
    return _load_pickle("landuse_by_unit.pkl")


def load_density_by_unit():
    return _load_pickle("density_by_unit.pkl")


def load_gardens():
    return _load_pickle("gardens.pkl")


def load_ecocenters():
    return _load_pickle("ecocenters.pkl")


def load_mariane_annual():
    path = os.path.join(CACHE_DIR, "mariane_annual.pkl")
    if not os.path.exists(path):
        return pd.DataFrame(columns=["unit", "Year", "Matière corrigé", "Net"])
    return pd.read_pickle(path)


def load_bilan_massique_agglo():
    return pd.read_pickle(os.path.join(CACHE_DIR, "bilan_massique_agglo.pkl"))


def load_bilan_massique_by_unit():
    return pd.read_pickle(os.path.join(CACHE_DIR, "bilan_massique_by_unit.pkl"))


def load_historical_population():
    return pd.read_pickle(os.path.join(CACHE_DIR, "historical_population.pkl"))


def load_population():
    df = pd.read_csv(POPULATION_CSV, encoding="utf-8-sig")
    df["Code"] = df["Code"].astype(str)
    df.loc[df["Level"] == "Municipality", "Code"] = df.loc[df["Level"] == "Municipality", "Code"].str.zfill(5)
    return df
