import brightway2 as bw
import bw2io as bi

SCENARIO_DB_LOCATION = "data/brightway/Scenarios Database.xlsx"
OWM_DB_LOCATION = "data/brightway/Canada OWM Facilities Database.xlsx"
OWM_DATABASE = "OWM Facilities"

def refresh_scenarios(database_name):
    imp = bw.ExcelImporter(SCENARIO_DB_LOCATION) 
    imp.apply_strategies()
    imp.match_database(database_name, fields=('name', 'unit', 'location', 'reference product')) 
    imp.match_database(fields=('name', 'unit', 'location'))
    imp.statistics()
    imp.write_excel(only_unlinked=True)
    imp.write_database()

def initialization():
    """Method to initialize brightway database when first running the app"""
    PROJECT_NAME = "testproject8"
    DATABASE_NAME = "ecoinvent-3.9.1-cutoff"

    bw.projects.set_current(PROJECT_NAME)
    
    if DATABASE_NAME not in bw.databases:
        bw.bw2setup()
        print(bw.databases)
        bi.import_ecoinvent_release('3.9.1', 'cutoff','ebenezer.kwofie@mcgill.ca', '2EBz*!#0DCH4')
    
    if OWM_DATABASE not in bw.databases:
        imp = bi.ExcelImporter(r"data/brightway/Canada OWM Facilities Database.xlsx")
        imp.apply_strategies()
        imp.match_database(DATABASE_NAME, fields=('name', 'unit', 'location', 'reference product'))
        imp.match_database(fields=('name', 'unit', 'location'))
        imp.statistics()
        imp.write_excel(only_unlinked=True)
        imp.write_database()
    
    refresh_scenarios(OWM_DATABASE)