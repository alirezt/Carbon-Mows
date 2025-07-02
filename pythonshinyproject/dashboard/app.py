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

SCENARIO_DB_LOCATION = "data/Scenarios Database.xlsx"
OWM_DB_LOCATION = "data/Canada OWM Facilities Database.xlsx"
OWM_DATABASE = "OWM Facilities"

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
    PROJECT_NAME = "testproject7"
    DATABASE_NAME = "ecoinvent-3.9.1-cutoff"

    bw.projects.set_current(PROJECT_NAME)
    
    if DATABASE_NAME not in bw.databases:
        bw.bw2setup()
        print(bw.databases)
        bi.import_ecoinvent_release('3.9.1', 'cutoff','ebenezer.kwofie@mcgill.ca', '2EBz*!#0DCH4')
    
    if OWM_DATABASE not in bw.databases:
        imp = bi.ExcelImporter(r"data/Canada OWM Facilities Database.xlsx")
        imp.apply_strategies()
        imp.match_database(DATABASE_NAME, fields=('name', 'unit', 'location', 'reference product'))
        imp.match_database(fields=('name', 'unit', 'location'))
        imp.statistics()
        imp.write_excel(only_unlinked=True)
        imp.write_database()
    
    refresh_scenarios(OWM_DATABASE)

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

                    if pd.notna(curr_row[0]) and str(curr_row[0]).strip() == "Activity": 
                        break
                    
                    if pd.notna(curr_row[0]) and str(curr_row[0]).strip() == "Exchanges":
                        exchanges = True
                        curr += 3 

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

                scenario_id = f"scenario_{abs(hash(scenario_name + str(index) + str(random.randrange(15000))))}"
                
                scenarios.append({
                    'name': scenario_name,
                    'row': index + 1,
                    'components': components,
                    'id': scenario_id
                })

    except Exception as e:
        print(f"ERROR: {e}")
    

    return scenarios

def save_scenario_to_database(name, description, components):
    try:
        workbook = openpyxl.load_workbook(SCENARIO_DB_LOCATION, data_only=False)  
        ws = workbook['Sheet1']

        last_row = 0
        for row_num in range(1, ws.max_row + 1):
            if ws.cell(row=row_num, column=1).value is not None or ws.cell(row=row_num, column=2).value is not None:
                last_row = row_num
        
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
            row_num = start_row + i
            for col_idx, value in enumerate(new_row):
                if col_idx < 9:  
                    ws.cell(row=row_num, column=col_idx + 1, value=value)
        
        workbook.save(SCENARIO_DB_LOCATION)
        workbook.close()

        return 1
    
    except Exception as e:
        print(e)
        return 0

def delete_scenario_from_database(name):
    print(f"deleting {name}")
    try:
        workbook = openpyxl.load_workbook(SCENARIO_DB_LOCATION, data_only=False)  # Keep formulas
        ws = workbook['Sheet1']

        start_row = None
        end_row = ws.max_row + 1

        for row_num in range(1, ws.max_row + 1):
            cell_value = ws.cell(row=row_num, column=1).value
            if cell_value == "Activity":
                scenario_name_cell = ws.cell(row=row_num, column=2).value
                if scenario_name_cell == name:
                    start_row = row_num
                    break
        
        if start_row is None:
            print(f"Scenario '{name}' not found")
            workbook.close()
            return 0
        
        for row_num in range(start_row + 1, ws.max_row + 1):
            cell_value = ws.cell(row=row_num, column=1).value
            if cell_value == "Activity":
                end_row = row_num
                break
    
        rows_to_delete = end_row - start_row

        print(start_row)
        print(end_row)

        for _ in range(rows_to_delete):
            ws.delete_rows(start_row)
        
        workbook.save(SCENARIO_DB_LOCATION)
        workbook.close()

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
            ui.div(
                ui.h5("Components"),
                ui.hr(class_="my-3"),
                class_="mt-4"
            ),
            ui.output_ui("list_of_components"),
            title="Scenarios",

            #class_="bg-light"
        ),
        ui.output_ui("lca_value_cards"),
        ui.card(
             ui.card_header("Scenario Life Cycle Assesement Graph"),
             ui.output_plot("lca_plot"),
             class_="shadow-sm"
        ),
        ui.card(
            ui.card_header("Scenario Life Cycle Assesement Contribution Analysis"),
            ui.output_plot("contribution_plot"),
            class_="shadow-sm"
        ),
        ui.card(
            ui.card_header("Components Life Cycle Assesement Graph"),
            ui.output_plot("components_lca_plot"),
            class_="shadow-sm"
        ),
        ui.output_ui("lca_component_value_cards"),
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
    deletion_in_progress = reactive.Value(False)
    contribution_results = reactive.Value(None)

    #Components Analysis Values

    components_results = reactive.Value(None)
    components_last_change_time = reactive.Value(0)
    selected_components = reactive.Value([])

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
    def track_component_checkbox_changes():
        c_list = get_available_components()
        for index, _ in enumerate(c_list):
            check_id = f"sidebar_component_{index}"
            if check_id in input:
                input[check_id]()
        
        components_last_change_time.set(time.time())

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
            l = [a for a in LCAdb if name == a['name']]
            list_of.append(l)
        
        acts = tuple(activities[0] for activities in list_of if activities)
        
        CC_method = [m for m in bw.methods if 'IPCC 2021' in str(m) and not 'LT' in str(m) and 'GWP100' in str(m) and 'climate change' in str(m) and not 'biogenic' in str(m) and not 'fossil' in str(m) and not 'land use' in str(m) and not 'SLCFs' in str(m)]

        #LCA

        if acts != ():
            FU = [{x:1} for x in acts] 
            bw.calculation_setups['OWM_Scenarios'] = {'inv':FU, 'ia': CC_method}
            mylca = bw.MultiLCA('OWM_Scenarios')

            mylcadf = pd.DataFrame(index = CC_method, columns = [(x['name']) for y in FU for x in y], data=mylca.results.T)
            
            df = mylcadf.copy()
            df.index = ['IPCC 2021' if 'IPCC 2021' in str(idx) else str(idx) for idx in df.index]
            
            lca_results.set(df)
        else:
            lca_results.set(None)
        
        #Contribution Analysis

        if acts != ():

            act = bw.Database(acts[0]['database']).get(acts[0]['code'])
            functional_unit = {act: 1} 
            mymethod = CC_method[0]
            lca = bw.LCA(functional_unit, mymethod)
            lca.lci()
            lca.lcia()

            def dolcacalc(act, mydemand, mymethod):
                my_fu = {act: mydemand} 
                lca = bw.LCA(my_fu, mymethod)
                lca.lci()
                lca.lcia()
                return lca.score

            def getLCAresults(list_acts, mymethod):
                
                all_activities = []
                results = []
                for a in list_acts:
                    act = bw.Database(a[0]).get(a[1])
                    print(act)
                    all_activities.append(act['name'])
                    results.append(dolcacalc(act,1,mymethod)) # 1 stays for one unit of each process
                    #print(act['name'])
                
                results_dict = dict(zip(all_activities, results))
                
                return results_dict

            ca_dict = {}

            for act in acts:
                
                exc_list = []
                contr_list = []

                for exc in list(act.exchanges()):
                    
                    if exc['type'] == 'biosphere':
                        
                        col = lca.activity_dict[exc['output']] # find column index of A matrix for the activity
                        row = lca.biosphere_dict[exc['input']] # find row index of B matrix for the exchange
                        contr_score = lca.biosphere_matrix[row,col] * lca.characterization_matrix[row,row]
                        contr_list.append((exc['input'],exc['type'], exc['amount'], contr_score))
                        
                    elif exc['type'] == 'substitution':
                        
                        contr_score = dolcacalc(bw.Database(exc['input'][0]).get(exc['input'][1]), exc['amount'], mymethod)
                        contr_list.append((exc['name'],exc['input'], exc['type'], exc['amount'], -contr_score))
                        
                    else:
                        
                        contr_score = dolcacalc(bw.Database(exc['input'][0]).get(exc['input'][1]), exc['amount'], mymethod)
                        contr_list.append((exc['name'], exc['input'], exc['type'], exc['amount'], contr_score))
                    
                ca_dict[act['name']] =  contr_list

            contribution_tables = {}  # Dictionary to store tables for each scenario

            for act in acts:
                name = act['name']
                df = pd.DataFrame(ca_dict[name], columns=['name', 'input', 'type', 'amount', 'contribution'])

                production_total = df.loc[df['type'] == 'production', 'contribution'].sum()
                df['%_contribution'] = 100 * df['contribution'] / production_total

                df = df.sort_values(by='contribution', ascending=False)

                contribution_tables[name] = df


            all_scenarios_df = []

            for act in acts:
                scenario_name = act['name']
                df_temp = pd.DataFrame(ca_dict[scenario_name], columns=['name', 'input', 'type', 'amount', 'contribution'])
                df_temp = df_temp[df_temp['type'] == 'technosphere'].copy()
                df_temp['Scenario'] = scenario_name  # Add scenario label
                all_scenarios_df.append(df_temp)

            combined_df = pd.concat(all_scenarios_df, ignore_index=True)
            print(combined_df)

            contributions = [combined_df, mylca]
            contribution_results.set(contributions)
        else:
            contribution_results.set(None)

    @reactive.Effect
    def update_components_graph():
        current_time = time.time()
        change_time = components_last_change_time()
        
        if current_time - change_time < 1:  
            reactive.invalidate_later(0.1)
            return
        
        components = get_available_components()
        selected = []

        for index, scenarios in enumerate(components):
            check_id = f"sidebar_component_{index}"
            if check_id in input and input[check_id]():
                selected.append(scenarios)
        
        selected_components.set(selected)

        LCAdb = bw.Database("OWM Facilities")
        list_of = []

        for s in selected_components():
            l = [a for a in LCAdb if s in a['name']]
            list_of.append(l)
        
        acts = tuple(activities[0] for activities in list_of if activities)

        print(acts)
        
        CC_method = [m for m in bw.methods if 'IPCC 2021' in str(m) and not 'LT' in str(m) and 'GWP100' in str(m) and 'climate change' in str(m) and not 'biogenic' in str(m) and not 'fossil' in str(m) and not 'land use' in str(m) and not 'SLCFs' in str(m)]

        #LCA

        if acts != ():
            FU = [{x:1} for x in acts] 
            bw.calculation_setups['OWM_Scenarios'] = {'inv':FU, 'ia': CC_method}
            mylca = bw.MultiLCA('OWM_Scenarios')

            mylcadf = pd.DataFrame(index = CC_method, columns = [(x['name']) for y in FU for x in y], data=mylca.results.T)
            
            df = mylcadf.copy()
            df.index = ['IPCC 2021' if 'IPCC 2021' in str(idx) else str(idx) for idx in df.index]
            
            components_results.set(df)
        else:
            components_results.set(None)
        

        

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
    
    @reactive.Effect  
    def delete_scenario():
        if deletion_in_progress():
            return
            
        s_list = scenarios_rv()
        
        for scenario in s_list:
            delete_btn_id = f"delete_btn_{scenario['id']}"
            
            if delete_btn_id in input:
                button_clicks = input[delete_btn_id]()
                
                if button_clicks and button_clicks > 0:
                    deletion_in_progress.set(True)
                    
                    scenario_name = scenario['name']
                    print(f"Deleting scenario: {scenario_name}")
                    
                    success = delete_scenario_from_database(scenario_name)
                    
                    if success:
                        scenarios_rv.set(detect_scenarios())

                        if scenarios_rv() != []:
                            refresh_scenarios(OWM_DATABASE)  
                        print(f"Successfully deleted scenario: {scenario_name}")
                    else:
                        print(f"Failed to delete scenario '{scenario_name}'")
                    
                    deletion_in_progress.set(False)
                    return  
                                
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
            collapse_id = f"collapse_{scenario['id']}" 
            
            scenario_items.append(
                ui.div(
                    ui.input_action_button(
                    f"delete_btn_{scenario['id']}", 
                    "×",
                    class_="delete-scenario-btn",
                    title="Delete scenario"
                    ),
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
    @render.ui
    def list_of_components():
        available_components = get_available_components()

        component_checkboxes = []
    
        for i, component in enumerate(available_components):
            component_checkboxes.append(
                ui.div(
                    ui.input_checkbox(
                        f"sidebar_component_{i}",
                        component,
                        value=False
                    ),
                    class_="component-checkbox-item"
                )
            )
        
        return ui.div(
            *component_checkboxes,
            ui.div(
                ui.p(f"{len(available_components)} components available", 
                    class_="text-muted small mt-3")
            )
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
    @render.plot
    def contribution_plot():
        dfs = contribution_results()

        if dfs is None:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'Select scenarios to display results', 
                   ha='center', va='center', transform=ax.transAxes,
                   fontsize=14, color='gray')
            ax.set_xticks([])
            ax.set_yticks([])
            return fig
        else:
            df = dfs[0]
            pivot_df = df.pivot_table(index='Scenario', columns='name', values='contribution', aggfunc='sum')
            pivot_df = pivot_df.fillna(0)  

            fig, ax = plt.subplots(figsize=(14, 8))
            
            pivot_df.plot(
                kind='bar',
                stacked=True,
                ax=ax,  
                colormap='tab20',
                width=0.7
            )

            scenario_names = pivot_df.index.tolist()

            lcas = dfs[1]
            total_scores = [lcas.results[i][0] for i in range(len(scenario_names))]  # assumes 1 method, 3 scenarios

            for i, score in enumerate(total_scores):
                ax.scatter(
                    i,                     
                    score,                 
                    marker='D',            
                    color='black',
                    s=100,  # Make the marker bigger
                    label='Total Score' if i == 0 else "",  
                    zorder=5
                )

            ax.set_xlabel('', fontsize=12)
            ax.set_ylabel('Impact contribution (kg CO2-eq)', fontsize=12)
            ax.set_xticklabels(ax.get_xticklabels(), rotation=0)
            ax.legend(title='Facility / Total', bbox_to_anchor=(1.05, 1), loc='upper left')
            ax.grid(True, alpha=0.3, linestyle='--')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            
            plt.tight_layout(pad=1.5)
            
            return fig  
    
    @output
    @render.plot
    def components_lca_plot():
        df = components_results()
        if df is None:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'Select components to display results', 
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

    @output
    @render.ui
    def lca_component_value_cards():
        df = components_results()
        
        if df is None or df.empty:
            return ui.div()  
        
        icon_keys = ["seedling", "bolt", "earth", "leaf", "recycle", "industry"]
        
        value_boxes = []
        
        for idx, col in enumerate(df.columns):  
            value = df.iloc[0, idx] 
            formatted_value = f"{value:.1f}"
            
            icon_key = icon_keys[idx % len(icon_keys)]
            
            value_boxes.append(
                ui.value_box(
                    title=f"Component {col}",
                    value=formatted_value,
                    showcase=ICONS[icon_key],
                )
            )
        
        return ui.layout_columns(*value_boxes, fill=False)




app = App(app_ui, server)
