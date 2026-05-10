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
               # ui.input_checkbox("show_cadastral", "Cadastral Units", value=False),
                #ui.input_checkbox("show_montreal_buildings", "Montreal Buildings (Microsoft)", value=False),
                ui.input_checkbox("show_osm_buildings", "OpenStreetMap Buildings", value=False),
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
    
    MONTREAL_LAT = 45.5017
    MONTREAL_LON = -73.5673

    # Configuration for each shapefile
    SHAPEFILE_CONFIG = {
        "borough_boundaries": {
            "path": "data/shapefiles/Borough/borough_boundaries.shp",
            "name": "Borough Boundaries",
            "color": "blue",
            "weight": 2,
            "fillOpacity": 0.3
        },
       # "cadastral": {
        #    "path": "data/shapefiles/CadastralBF/uniteevaluationfonciere.shp",
         #   "name": "Cadastral Units",
          #  "color": "red",
           # "weight": 1,
            #"fillOpacity": 0.2
        #},
        # "montreal_buildings": {
        #     "path": "data/shapefiles/MicrosoftBF/Montreal_Microsoft.shp",
        #     "name": "Montreal Buildings",
        #     "color": "green",
        #     "weight": 1,
        #     "fillOpacity": 0.4
        # },
        "osm_buildings": {
            "path": "data/shapefiles/OpenStreetMapBF/gis_osm_buildings_a_free_1.shp",
            "name": "OSM Buildings",
            "color": "purple",
            "weight": 1,
            "fillOpacity": 0.3
        }
    }

    # Store layers as reactive values
    layers_store = reactive.Value({})
    
    def load_shapefile(shapefile):
        try:
            gdf = gpd.read_file(shapefile)
            if gdf.crs != 'EPSG:4326':
                gdf = gdf.to_crs('EPSG:4326')
            return json.loads(gdf.to_json())
        except Exception as e:
            print(f"Error loading shapefile {shapefile}: {e}")
            return None
    
    def create_geolayer(geodata, name, color='blue', weight=2, fillOpacity=0.3):
        if geodata is None:
            return None
        
        layer = L.GeoJSON(
            data=geodata,
            style={
                'color': color,
                'weight': weight,
                'fillOpacity': fillOpacity,
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
    
    def get_or_create_layer(layer_id):
        current_layers = layers_store.get()
        
        if layer_id not in current_layers:
            config = SHAPEFILE_CONFIG[layer_id]
            geojson_data = load_shapefile(config["path"])
            
            if geojson_data:
                layer = create_geolayer(
                    geojson_data, 
                    layer_id,
                    color=config["color"],
                    weight=config["weight"],
                    fillOpacity=config["fillOpacity"]
                )
                current_layers[layer_id] = layer
                layers_store.set(current_layers)
                print(f"Created {config['name']} layer with {len(geojson_data['features'])} features")
            else:
                print(f"Failed to load {config['name']}")
                return None
        
        return current_layers[layer_id]
    
    def toggle_layer(layer_id, show):
        layer = get_or_create_layer(layer_id)
        if layer is None:
            print(f"Layer {layer_id} is None")
            return
        
        map_widget = montreal_map.widget
        
        if show:
            if layer not in map_widget.layers:
                map_widget.add_layer(layer)
                print(f"Added {SHAPEFILE_CONFIG[layer_id]['name']} layer to map")
        else:
            if layer in map_widget.layers:
                map_widget.remove_layer(layer)
                print(f"Removed {SHAPEFILE_CONFIG[layer_id]['name']} layer from map")
    
    @reactive.effect
    @reactive.event(input.show_borough_boundaries)
    def toggle_borough_boundaries():
        toggle_layer("borough_boundaries", input.show_borough_boundaries())
    
    # @reactive.effect
    # @reactive.event(input.show_cadastral)
    # def toggle_cadastral():
    #     toggle_layer("cadastral", input.show_cadastral())
    
    # @reactive.effect
    # @reactive.event(input.show_montreal_buildings)
    # def toggle_montreal_buildings():
    #     toggle_layer("montreal_buildings", input.show_montreal_buildings())
    
    @reactive.effect
    @reactive.event(input.show_osm_buildings)
    def toggle_osm_buildings():
        toggle_layer("osm_buildings", input.show_osm_buildings())