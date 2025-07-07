from shiny import ui, render, reactive
import ipyleaflet as L 
from shinywidgets import output_widget, render_widget
import ipywidgets

def foodwaste_tab_ui():
    return ui.page_sidebar(
        ui.sidebar(
            ui.div()
        ),
        output_widget("montreal_map"),
        ui.h1("Test")
    )

def foodwaste_tab_server(input, output, session):
    
    MONTREAL_LAT = 45.5017
    MONTREAL_LON = -73.5673
    
    @render_widget
    def montreal_map():
        m = L.Map(
            center=[MONTREAL_LAT, MONTREAL_LON],
            zoom=10,
            basemap=L.basemaps.OpenStreetMap.Mapnik,
            layout=ipywidgets.Layout(height='70vh')
        )
        
        m.add_control(L.ScaleControl(position="bottomleft"))
        m.add_control(L.FullScreenControl())
        
        return m