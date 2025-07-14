from shiny import ui, render, reactive
import ipyleaflet as L 
from shinywidgets import output_widget, render_widget
import ipywidgets
import geopandas as gpd
import json

def foodwaste_tab_ui():
    return ui.page_sidebar(
        ui.sidebar(
            ui.div(
                ui.p("Select layers to display:", class_="text-muted small mb-2"),
                ui.input_checkbox("show_borough_boundaries", "Borough Boundaries", value=False),
                class_="mb-3"
            ),
            title="Map Layers"
        ),
        output_widget("montreal_map"),
        ui.h1("Test"),
        title="ICI Food Waste Analysis",
        fillable=True,
    )

def foodwaste_tab_server(input, output, session):
    
    SHAPEFILES = ["data/shapefiles/Borough/borough_boundaries.shp"]
    MONTREAL_LAT = 45.5017
    MONTREAL_LON = -73.5673

    borough_layer = reactive.Value(None)
    
    def load_shapefile(shapefile):
        try:
            gdf = gpd.read_file(shapefile)
            if gdf.crs != 'EPSG:4326':
                gdf = gdf.to_crs('EPSG:4326')
            return json.loads(gdf.to_json())
        except Exception as e:
            print(f"Error loading shapefile {shapefile}: {e}")
            return None
    
    def create_geolayer(geodata, name, color='blue'):
        if geodata is None:
            return None
        
        layer = L.GeoJSON(
            data=geodata,
            style={
                'color': color,
                'weight': 2,
                'fillOpacity': 0.3,
                'fillColor': color,
                'opacity': 1.0
            },
            name=name
        )
        return layer
    
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
    
    # Create the borough layer once
    @reactive.calc
    def get_borough_layer():
        if borough_layer.get() is None:
            geojson_data = load_shapefile(SHAPEFILES[0])
            if geojson_data:
                layer = create_geolayer(geojson_data, "borough_boundaries", color='blue')
                borough_layer.set(layer)
                print(f"Created borough layer with {len(geojson_data['features'])} features")
        return borough_layer.get()
    
    @reactive.effect
    @reactive.event(input.show_borough_boundaries)
    def toggle_borough_layer():
        layer = get_borough_layer()
        if layer is None:
            print("Borough layer is None")
            return
        
        map_widget = montreal_map.widget
        
        if input.show_borough_boundaries():
            if layer not in map_widget.layers:
                map_widget.add_layer(layer)
                print("Added borough layer to map")
                
                
        else:
            if layer in map_widget.layers:
                map_widget.remove_layer(layer)
                print("Removed borough layer from map")