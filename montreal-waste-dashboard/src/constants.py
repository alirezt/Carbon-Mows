import os

DASH_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(DASH_BASE, "data", "cache")
ADMIN_UNITS_PKL = os.path.join(DASH_BASE, "data", "admin_units_mtm8.pkl")
POPULATION_CSV = os.path.join(DASH_BASE, "data", "population_long.csv")

# borough/municipality abbreviations, matching the user's existing R analysis convention
UNIT_ABBR = {
    "Ahuntsic-Cartierville": "AC",
    "Anjou": "AJ",
    "Baie-D'Urfé": "BU",
    "Beaconsfield": "BF",
    "Côte-des-Neiges - Notre-Dame-de-Grâce": "CN",
    "Côte-Saint-Luc": "CL",
    "Dollard-des-Ormeaux": "DO",
    "Dorval": "DV",
    "Hampstead": "HS",
    "Kirkland": "KL",
    "Lachine": "LC",
    "LaSalle": "LS",
    "Le Plateau-Mont-Royal": "PM",
    "Le Sud-Ouest": "SO",
    "LÎle-Bizard - Sainte-Geneviève": "IB",
    "Mercier - Hochelaga-Maisonneuve": "MH",
    "Montréal-Est": "ME",
    "Montréal-Nord": "MN",
    "Montréal-Ouest": "MO",
    "Mont-Royal": "MR",
    "Outremont": "OU",
    "Pierrefonds - Roxboro": "PR",
    "Pointe-Claire": "PC",
    "Rivière-des-Prairies - Pointe-aux-Trembles": "RP",
    "Rosemont - La Petite-Patrie": "RPP",
    "Sainte-Anne-de-Bellevue": "SB",
    "Saint-Laurent": "SL",
    "Saint-Léonard": "SE",
    "Senneville": "SN",
    "Verdun": "VD",
    "Ville-Marie": "VM",
    "Villeray - Saint-Michel - Parc-Extension": "VS",
    "Westmount": "WM",
    "L'Île-Dorval": "ID",
}

MATIERE_EN = {
    "Résidus alimentaires": "Food waste",
    "Matières organiques": "Organic matter",
}

AFFECTATIO_COLORS = {
    "Dominante résidentielle": "#2a78d6",
    "Activités diversifiées": "#1baf7a",
    "Industrie": "#eda100",
    "Agricole": "#008300",
    "Conservation": "#4a3aa7",
    "Grand espace vert ou récréation": "#e34948",
    "Grande emprise ou grande infrastructure publique": "#e87ba4",
    "Centre-ville d'agglomération": "#eb6834",
}

DENSITE_COLORS = {
    "8": "#f4f0fb", "10": "#ded1f4", "35": "#c3b0ea", "40": "#a88fe0",
    "60": "#8d6ed6", "80": "#7250c4", "110": "#5936a8", "150": "#3e1f80",
}

TYPE_COLORS = {"Borough": "#2a78d6", "Municipality": "#1baf7a"}

# residential units per parcel (NOMBRE_LOG), used as a population-density proxy
PARCEL_UNITS_BINS = [
    (0, 0, "No units / non-residential"),
    (1, 1, "1 unit"),
    (2, 3, "2-3 units"),
    (4, 8, "4-8 units"),
    (9, 20, "9-20 units"),
    (21, None, "21+ units"),
]
PARCEL_UNITS_COLORS = {
    "No units / non-residential": "#e8e6e1",
    "1 unit": "#fee5d9",
    "2-3 units": "#fcae91",
    "4-8 units": "#fb6a4a",
    "9-20 units": "#de2d26",
    "21+ units": "#a50f15",
}


def parcel_units_bin(n):
    for lo, hi, label in PARCEL_UNITS_BINS:
        if n >= lo and (hi is None or n <= hi):
            return label
    return PARCEL_UNITS_BINS[-1][2]


# population growth scenarios (ISQ Pop_Total_MUN_2025.xlsx), 2021-2041
SCENARIO_EN = {
    "Référence (A2025)": "Reference",
    "Faible (D2025)": "Low",
    "Fort (E2025)": "High",
}
SCENARIO_COLORS = {
    "Référence (A2025)": "#2a78d6",
    "Faible (D2025)": "#1baf7a",
    "Fort (E2025)": "#e34948",
}
HISTORICAL_POP_COLOR = "#333333"

# waste timeseries: colored by material, line style by source
MARIANE_MATERIAL_COLORS = {
    "Résidus alimentaires": "#2a78d6",
    "Matières organiques": "#1baf7a",
}
BILAN_MASSIQUE_COLOR = "#eda100"
BILAN_MASSIQUE_ALIASES = {
    "Plateau-Mont-Royal (Le)": "Le Plateau-Mont-Royal",
    "Sud-Ouest (Le)": "Le Sud-Ouest",
}

# decorative selectors — not yet wired to any dataset
DECENTRALIZATION_OPTIONS = ["Highly decentralised", "Moderately centralised", "Highly centralised"]
LU_MOBILITY_OPTIONS = ["50%", "80%", "100% (2050)"]
