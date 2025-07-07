from shiny import ui, render, reactive

def foodwaste_tab_ui():
    return ui.div(
        ui.h2("Foodwaste Tab Content")
    )

def foodwaste_tab_server(input, output, session):
    ...