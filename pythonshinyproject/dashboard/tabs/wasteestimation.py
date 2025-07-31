from shiny import ui, render, reactive

def wasteestimation_tab_ui():
    return ui.page_sidebar(
        ui.sidebar(
            ui.div(

            )
        ),
        title="Waste Estimation"
    )

def wasteestimation_tab_server(input, output, session):
    ...