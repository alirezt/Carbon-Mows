import brightway2 as bw
import bw2io as bi
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
from faicons import icon_svg
import openpyxl
import random

# Import data from shared.py
from shared import app_dir

from shiny import App, reactive, render, ui

# Import tab modules
from tabs.brightwaytab import brightway_tab_ui, brightway_tab_server
from tabs.foodwastetab import foodwaste_tab_ui, foodwaste_tab_server
from init import initialization

# Initialize the application
initialization()

# Define the main UI
app_ui = ui.page_fluid(
    ui.navset_tab(
        ui.nav_panel("Brightway LCA", brightway_tab_ui()),
        ui.nav_panel("Foodwaste", foodwaste_tab_ui()),
    ),
    ui.include_css(app_dir / "styles.css"),
)

def server(input, output, session):
    brightway_tab_server(input, output, session)
    foodwaste_tab_server(input, output, session)


app = App(app_ui, server)