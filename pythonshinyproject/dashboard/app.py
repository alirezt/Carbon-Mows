import brightway2 as bw
import bw2io as bi
import pandas as pd
import matplotlib.pyplot as plt

# Import data from shared.py
from shared import app_dir

from shiny import App, reactive, render, ui

SCENARIO_DB_LOCATION = "data/Scenarios Database.xlsx"

def refresh_scenarios(database_name):
    imp = bw.ExcelImporter(SCENARIO_DB_LOCATION) 
    imp.apply_strategies()
    imp.match_database(database_name, fields=('name', 'unit', 'location', 'reference product')) 
    imp.match_database(fields=('name', 'unit', 'location'))
    imp.statistics()
    imp.write_excel(only_unlinked=True)
    imp.write_database()

def initialization():
    """Method to initialize brightway databse when first running the app"""
    PROJECT_NAME = "testproject5"
    DATABASE_NAME = "ecoinvent-3.8-cutoff"
    OWM_DATABASE = "OWM LCA"

    bw.projects.set_current(PROJECT_NAME)

    if DATABASE_NAME not in bw.databases:
        bw.bw2setup()
        print(bw.databases)
        bi.import_ecoinvent_release('3.8', 'cutoff','ebenezer.kwofie@mcgill.ca', '2EBz*!#0DCH4')
    
    if OWM_DATABASE not in bw.databases:
        imp = bi.ExcelImporter(r"data/Canada OWM Facilities Database.xlsx")
        imp.apply_strategies()
        imp.match_database(DATABASE_NAME, fields=('name', 'unit', 'location', 'reference product'))
        imp.match_database(fields=('name', 'unit', 'location'))
        imp.statistics()
        imp.write_excel(only_unlinked=True)
        imp.write_database()
    
    for db_name in bw.databases:
        print(f"Processing database: {db_name}")
        db = bw.Database(db_name)
        if hasattr(db, 'process'):
            db.process()
    
    refresh_scenarios(OWM_DATABASE)

initialization()

def detect_scenarios():
    """Method to detect scenarios in the Scenario Database, easy implementation for now"""
    scenarios = []

    try:
        df = pd.read_excel(SCENARIO_DB_LOCATION, header=None, sheet_name="Sheet1")

        for index, row in df.iterrows():
            if pd.notna(row[0]) and str(row[0]).strip() == "Activity":
                scenario_name = str(row[1]).strip()
                scenarios.append({
                    'name': scenario_name,
                    'row': index + 1
                })

    except Exception as e:
        print(f"ERROR: {e}")
    
    return scenarios

def brightway_tab():
    return ui.page_sidebar(
        ui.sidebar(
            ui.output_ui("list_of_scenarios"),
            title="Scenarios",
        ),
        ui.output_plot("lca_plot"),
        title="Canada OWM Facilities",
        fillable=True,
    )

def test2_tab():
    return ui.div(
        ui.h2("Test 2 Content"),
        ui.p("This is the second tab"),
    )

def test3_tab():
    return ui.div(
        ui.h2("Test 3 Content"),
        ui.p("This is the third tab"),
    )

app_ui = ui.page_fluid(
    ui.navset_tab(
        ui.nav_panel("Brightway LCA", brightway_tab()),
        ui.nav_panel("Test2", test2_tab()),
        ui.nav_panel("Test3", test3_tab()),
    ),
    ui.include_css(app_dir / "styles.css"),
)

# Your server function remains the same
def server(input, output, session):
    scenarios_rv = reactive.Value(detect_scenarios())
    selected_scenarios = reactive.Value([])
    lca_results = reactive.Value(None)

    @reactive.Effect
    def update_graph():
        s_list = scenarios_rv()
        selected = []

        for index, scenarios in enumerate(s_list):
            check_id = f"check_scenario_{index}"
            if check_id in input and input[check_id]():
                selected.append(scenarios)
        
        selected_scenarios.set(selected)

        LCAdb = bw.Database("Scenarios")
        list_of = []

        for s in selected_scenarios():
            name = s["name"]
            l = [a for a in LCAdb if name in a['name']]
            list_of.append(l)
        
        acts = tuple(activities[0] for activities in list_of if activities)
        
        CC_method = [m for m in bw.methods if 'IPCC 2013' in str(m) and not 'LT' in str(m) and 'GWP 100' in str(m)]
    
        if acts != ():
            FU = [{x:1} for x in acts] 
            bw.calculation_setups['OWM_Scenarios'] = {'inv':FU, 'ia': CC_method}
            mylca = bw.MultiLCA('OWM_Scenarios')
            print(mylca.results)

            mylcadf = pd.DataFrame(index = CC_method, columns = [(x['name']) for y in FU for x in y], data=mylca.results.T)
            df = mylcadf
            lca_results.set(df)
        else:
            lca_results.set(None)


    @output
    @render.ui
    def list_of_scenarios():
        s_list = scenarios_rv()

        if len(s_list) == 0:
            return ui.div(
                ui.p("Use the Add button to add a Scenario", class_="text-muted")
            )
        
        scenario_items = []
        for index, scenario in enumerate(s_list):
            scenario_items.append(
                ui.div(
                    ui.input_checkbox(
                        f"check_scenario_{index}",
                        scenario['name'],
                        value=False
                    ),
                    class_="mb-2"
                )
            )
        
        return ui.div(
            *scenario_items
        )
    
    @output
    @render.plot
    def lca_plot():
        df = lca_results()

        if df is None:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'Select scenarios to display results', 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=14, color='gray')
            ax.set_xticks([])
            ax.set_yticks([])
            return fig
        else:
            fig =  df.plot.bar(
                xlabel='Impact category',
                ylabel='Impact score (kg CO2-eq)',
                figsize=(14,8)
            )
        
        return fig






app = App(app_ui, server)
