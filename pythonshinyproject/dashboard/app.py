import brightway2 as bw
import bw2io as bi
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import time
from faicons import icon_svg
import openpyxl

# Import data from shared.py
from shared import app_dir

from shiny import App, reactive, render, ui

SCENARIO_DB_LOCATION = "data/Scenarios Database.xlsx"
OWM_DB_LOCATION = "data/Canada OWM Facilities Database.xlsx"
OWM_DATABASE = "OWM LCA"

ICONS = {
    "industry": icon_svg("industry"),
    "recycle": icon_svg("recycle"), 
    "leaf": icon_svg("leaf"),
    "earth": icon_svg("earth-americas"),
    "bolt": icon_svg("bolt"),
    "seedling": icon_svg("seedling"),
}

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
    
    #refresh_scenarios(OWM_DATABASE)

initialization()

def detect_scenarios():
    """Method to detect scenarios in the Scenario Database, easy implementation for now"""
    scenarios = []

    try:
        df = pd.read_excel(SCENARIO_DB_LOCATION, header=None, sheet_name="Sheet1")

        for index, row in df.iterrows():
            if pd.notna(row[0]) and str(row[0]).strip() == "Activity":
                components = []

                scenario_name = str(row[1]).strip()

                exchanges = False
                curr = index + 1

                while curr < len(df):
                    curr_row = df.iloc[curr]

                    if pd.notna(curr_row[0]) and str(curr_row[0]).strip() == "Activity": #Reached next Scenario
                        break
                    
                    if pd.notna(curr_row[0]) and str(curr_row[0]).strip() == "Exchanges":
                        exchanges = True
                        curr += 3 #Skip Header and Component Name

                        continue

                    if exchanges and pd.notna(curr_row[0]):
                        component_name = str(curr_row[0]).strip()

                        if pd.notna(curr_row[2]):
                            try:
                                percentage = float(curr_row[3])
                                components.append({
                                    'name': component_name,
                                    'percentage': percentage
                                })
                            except (ValueError, TypeError):
                                print("Excel Format Not Appropriate")
                                pass
                    
                    curr += 1

                scenarios.append({
                    'name': scenario_name,
                    'row': index + 1,
                    'components': components
                })

    except Exception as e:
        print(f"ERROR: {e}")
    
    print(scenarios)

    return scenarios

def save_scenario_to_database(name, description, components):
    try:
        df = pd.read_excel(SCENARIO_DB_LOCATION, header=None, sheet_name="Sheet1")

        last_row = 0
        for index, row in df.iterrows():
            if pd.notna(row[0]) or pd.notna(row[1]):  
                last_row = index
        
        start_row = last_row + 5

        new_rows = []

        activity_row = [""] * 9
        activity_row[0] = "Activity"
        activity_row[1] = name

        new_rows.append(activity_row)

        metadata_rows = [
            ["comment", description, "", "", "", "", "", "", ""],
            ["location", "CA-QC", "", "", "", "", "", "", ""],
            ["production amount", "1", "", "", "", "", "", "", ""],
            ["unit", "tonne", "", "", "", "", "", "", ""],
            ["", "", "", "", "", "", "", "", ""],  
        ]

        new_rows.extend(metadata_rows)
        new_rows.append(["Exchanges", "", "", "", "", "", "", "", ""])
        new_rows.append(["name", "reference product", "unit", "amount", "location", "database", "type", "categories", "comment"])

        new_rows.append([name, "OFMSW", "tonne", "1", "CA-QC", "Scenarios", "production", "", ""])

        for component in components:
            cname = component["name"]
            amount = component["percentage"] / 100.0

            component_row = [
                cname,           
                "OFMSW",            
                "tonne",            
                amount,         
                "CA-QC",            
                "OWM Facilities",   
                "technosphere",     
                "",                 
                "",                 
            ]

            new_rows.append(component_row)
        
        for i, new_row in enumerate(new_rows):
            row_index = start_row + i

            while len(df) <= row_index:
                df.loc[len(df)] = [""] * len(df.columns)
            
            for col_idx, value in enumerate(new_row):
                if col_idx < len(df.columns):
                    df.iloc[row_index, col_idx] = value
        
        with pd.ExcelWriter(SCENARIO_DB_LOCATION, engine='openpyxl', mode='w') as writer:
            df.to_excel(writer, sheet_name='Sheet1', index=False, header=False)
        
        return 1
    
    except Exception as e:
        print(e)
        return 0


def brightway_tab():
    return ui.page_sidebar(
        ui.sidebar(
            ui.output_ui("list_of_scenarios"),
            ui.input_action_button(
                "add_scenario_button",
                "Create Scenario",
                class_="btn-primary mb-3 w-100"
            ),
            title="Scenarios",
            #class_="bg-light"
        ),
        ui.output_ui("lca_value_cards"),
        ui.card(
             ui.card_header("Life Cycle Assesement Graph"),
             ui.output_plot("lca_plot"),
             class_="shadow-sm"
        ),
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

def server(input, output, session):
    scenarios_rv = reactive.Value(detect_scenarios())
    selected_scenarios = reactive.Value([])
    lca_results = reactive.Value(None)
    last_change_time = reactive.Value(0)

    def get_available_components():
        try:
            df = pd.read_excel(OWM_DB_LOCATION, header=None, sheet_name="LCI")
            components = []
            for index, row in df.iterrows():
                if pd.notna(row[0]) and str(row[0]).strip() == "Activity":
                    comp_name = str(row[1]).strip()
                    components.append(comp_name)

        except Exception as e:
            print(f"ERROR: {e}")
        
        return components

    @reactive.Effect
    def track_checkbox_changes():
        s_list = scenarios_rv()
        for index, _ in enumerate(s_list):
            check_id = f"check_scenario_{index}"
            if check_id in input:
                input[check_id]()  
        
        last_change_time.set(time.time())

    @reactive.Effect
    def update_graph():
        current_time = time.time()
        change_time = last_change_time()
        
        if current_time - change_time < 1:  
            reactive.invalidate_later(0.1)
            return
        
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
            
            df = mylcadf.copy()
            df.index = ['IPCC 2013' if 'IPCC 2013' in str(idx) else str(idx) for idx in df.index]
            
            lca_results.set(df)
        else:
            lca_results.set(None)

    @reactive.Effect
    @reactive.event(input.add_scenario_button)
    def show_add_scenario_form():
        available_components = get_available_components()
        modal = ui.modal(
            ui.div(
                ui.h4("Create New Scenario", class_="mb-3"),
                ui.hr(),
                
                ui.div(
                    ui.input_text(
                        "scenario_name",
                        "Scenario Name:",
                        placeholder="Enter scenario name...",
                        value=""
                    ),
                    class_="mb-4"
                ),

                ui.div(
                    ui.input_text(
                        "scenario_description",
                        "Description:",
                        placeholder="Enter description... (Optional)",
                        value=""
                    ),
                    class_="mb-4"
                ),


                ui.div(
                    ui.h5("Select Components:", class_="mb-3"),
                    ui.div(
                        [ui.input_checkbox(f"component_{i}", comp, value=False) 
                        for i, comp in enumerate(available_components)],
                        class_="component-checkboxes mb-3"
                    ),
                    class_="mb-4"
                ),

                ui.div(
                    ui.output_ui("component_sliders"),
                    class_="sliders-container"
                ),
            
                ui.div(
                    ui.output_ui("total_percentage"),
                    class_="mt-3"
                )
            ),
            footer=ui.div(
                ui.input_action_button(
                    "cancel_scenario", 
                    "Cancel", 
                    class_="btn-secondary me-2"
                ),
                ui.output_ui("save_button_dynamic"), 
            ),
            size="l",
            easy_close=True
        )
        ui.modal_show(modal)

    @output
    @render.ui
    def save_button_dynamic():
        available_components = get_available_components()
        
        total = 0
        selected_count = 0
        
        for i in range(len(available_components)):
            checkbox_id = f"component_{i}"
            slider_id = f"slider_{i}"
            
            if checkbox_id in input and input[checkbox_id]():
                selected_count += 1
                if slider_id in input:
                    total += input[slider_id]()
        
        scenario_name = input.scenario_name() if "scenario_name" in input else ""
        scenario_name = scenario_name.strip()
        
        existing_scenarios = scenarios_rv()
        existing_names = [scenario['name'].lower() for scenario in existing_scenarios]
        
        name_valid = (
            scenario_name != "" and  
            scenario_name.lower() not in existing_names  
        )
        
        is_enabled = (
            total == 100 and 
            name_valid and 
            selected_count > 0
        )
        
        if is_enabled:
            return ui.input_action_button(
                "save_scenario", 
                "Save Scenario", 
                class_="btn-primary"
            )
        else:
            return ui.input_action_button(
                "save_scenario_disabled", 
                "Save Scenario", 
                class_="btn-secondary",
                disabled=True
            )
        
    @output
    @render.ui
    def component_sliders():
        available_components = get_available_components()
        
        selected_components = []
        for i, comp in enumerate(available_components):
            checkbox_id = f"component_{i}"
            if checkbox_id in input and input[checkbox_id]():
                selected_components.append((i, comp))
        
        if not selected_components:
            return ui.div()
        
        sliders = []
        sliders.append(ui.h5("Component Allocation:", class_="mb-3"))
        
        for i, comp_name in selected_components:
            slider_id = f"slider_{i}"
            current_value = input[slider_id]() if slider_id in input else 0
            
            sliders.append(
                ui.div(
                    ui.input_slider(
                        slider_id,
                        comp_name,
                        min=1,
                        max=100,
                        value=current_value,
                        step=1,
                        post="%"
                    ),
                    class_="mb-2"
                )
            )
        
        return ui.div(*sliders)

    @output
    @render.ui  
    def total_percentage():
        available_components = get_available_components()
        
        total = 0
        selected_count = 0
        
        for i in range(len(available_components)):
            checkbox_id = f"component_{i}"
            slider_id = f"slider_{i}"
            
            if checkbox_id in input and input[checkbox_id]():
                selected_count += 1
                if slider_id in input:
                    total += input[slider_id]()
        
        if selected_count == 0:
            return ui.div()
        
        if total == 100:
            alert_class = "alert-success"
            icon = "✓"
            message = f"{icon} Total: {total}% - Perfect!"
        elif total < 100:
            alert_class = "alert-warning" 
            icon = "⚠"
            message = f"{icon} Total: {total}% - Need {100-total}% more"
        else:
            alert_class = "alert-danger"
            icon = "⚠"
            message = f"{icon} Total: {total}% - {total-100}% over limit!"
        
        return ui.div(
            ui.div(
                message,
                class_=f"alert {alert_class} mb-0"
            )
        )
          
    @reactive.Effect
    @reactive.event(input.cancel_scenario)
    def hide_add_scenario_form():
        ui.modal_remove()

    @reactive.Effect
    @reactive.event(input.save_scenario)
    def hide_save_form():
        scenario_name = input.scenario_name().strip()
        description = input.scenario_description().strip() if "scenario_description" in input else ""

        available_components = get_available_components()
        selected_components_data = []

        for i in range(len(available_components)):
            checkbox_id = f"component_{i}"
            slider_id = f"slider_{i}"
            
            if checkbox_id in input and input[checkbox_id]():
                if slider_id in input:
                    percentage = input[slider_id]()
                    selected_components_data.append({
                        'name': available_components[i],
                        'percentage': percentage
                    })

        success = save_scenario_to_database(scenario_name, description, selected_components_data)

        if success:
            refresh_scenarios(OWM_DATABASE)
            scenarios_rv.set(detect_scenarios())  
            print("Scenario Saved")
        else:
            print("Failed to save scenario")

        ui.modal_remove()

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
            components_display = []
            
            for component in scenario['components']:
                percentage = f"{component['percentage']:.2%}"
                components_display.append(
                    ui.div(
                        ui.span(component['name'], class_="component-name"),
                        ui.span(f" ({percentage})", class_="component-percentage text-muted"),
                        class_="component-item small"
                    )
                )
            
            components_count = len(scenario['components'])
            collapse_id = f"collapse_{index}"
            
            scenario_items.append(
                ui.div(
                    ui.div(
                        ui.div(
                            ui.input_checkbox(
                                f"check_scenario_{index}",
                                scenario['name'],
                                value=False
                            ),
                            class_="scenario-checkbox"
                        ),
                        ui.HTML(f"""
                            <button class="scenario-toggle-btn" 
                                    type="button" 
                                    data-bs-toggle="collapse" 
                                    data-bs-target="#{collapse_id}" 
                                    aria-expanded="false" 
                                    aria-controls="{collapse_id}">
                                <span class="component-count">({components_count})</span>
                                <i class="toggle-arrow">▼</i>
                            </button>
                        """),
                        class_="scenario-header"
                    ),
                    ui.div(
                        ui.div(
                            *components_display,
                            class_="components-list"
                        ),
                        class_="collapse",
                        id=collapse_id
                    ) if components_display else ui.div(),
                    class_="scenario-item mb-3"
                )
            )
        
        scenario_items.append(
            ui.div(
                ui.p(f"Select scenarios to analyze", class_="text-muted small mb-3"),
                ui.span(f"{len(s_list)} ", class_="text-muted small"),
                ui.span("available", class_="text-muted small")
            )
        )
        
        return ui.div(
            *scenario_items
        )

    @output
    @render.plot
    def lca_plot():
        df = lca_results()
        print(df)
        if df is None:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'Select scenarios to display results', 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=14, color='gray')
            ax.set_xticks([])
            ax.set_yticks([])
            return fig
        else:
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")

            fig, ax = plt.subplots(figsize=(14, 8))
            df.plot.bar(
                ax=ax,
                xlabel='Impact Category',
                ylabel='Impact Score (kg CO2-eq)',
                color=sns.color_palette("husl", len(df.columns)),
                alpha=0.8,
                width=0.7
            )

            ax.set_title('Life Cycle Assessment Results', fontsize=16, fontweight='bold', pad=20)
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
        
        return fig
    
    @output
    @render.ui
    def lca_value_cards():
        df = lca_results()
        
        if df is None or df.empty:
            return ui.div()  
        
        icon_keys = ["industry", "recycle", "leaf", "earth", "bolt", "seedling"]
        
        value_boxes = []
        
        for idx, col in enumerate(df.columns):  
            value = df.iloc[0, idx] 
            formatted_value = f"{value:.1f}"
            
            icon_key = icon_keys[idx % len(icon_keys)]
            
            value_boxes.append(
                ui.value_box(
                    title=f"Scenario {col}",
                    value=formatted_value,
                    showcase=ICONS[icon_key],
                )
            )
        
        return ui.layout_columns(*value_boxes, fill=False)




app = App(app_ui, server)
