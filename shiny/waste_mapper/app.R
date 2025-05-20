library(shiny)
library(leaflet)
library(sf)
library(dplyr)
library(ggplot2)
library(plotly)
library(stringr)
library(tidyr)

# Read and transform shapefiles
shape_data <- st_read("data/montreal_household_waste_collection_area/collecte-des-ordures-menageres.shp")
shape_data2 <- st_read("data/montreal_food_waste_collection_area/collecte-des-residus-alimentaires.shp")
shape_data3 <- st_read("data/montreal_admin_boundaries/limites-administratives-agglomeration.shp")
shape_data4 <- st_read("data/Montreal DA.shp")
shape_data5 <- st_read("data/Montreal Economic Region.shp")
shape_data6 <- st_read("data/Montreal ADA.shp")  

# Transform to WGS84 (EPSG:4326)
shape_data_wgs84 <- st_transform(shape_data, crs = 4326)
shape_data2_wgs84 <- st_transform(shape_data2, crs = 4326)
shape_data3_wgs84 <- st_transform(shape_data3, crs = 4326)
shape_data4_wgs84 <- st_transform(shape_data4, crs = 4326)
shape_data5_wgs84 <- st_transform(shape_data5, crs = 4326)
shape_data6_wgs84 <- st_transform(shape_data6, crs = 4326)  

# Add new shape data to the list
shapefile_list <- list(
  "Household Waste Collection Region" = shape_data_wgs84,
  "Food Waste Collection Region" = shape_data2_wgs84,
  "Montreal Administrative Boundaries" = shape_data3_wgs84,
  "Montreal Dissemination Areas" = shape_data4_wgs84,
  "Montreal Economic Region" = shape_data5_wgs84,
  "Montreal Aggregated Dissemination Areas" = shape_data6_wgs84  
)

ui <- fluidPage(
  titlePanel(tags$strong("Montreal Organic Waste Mapper")),
  
  tabsetPanel(
    tabPanel("Map",
             sidebarLayout(
               sidebarPanel(
                 width = 3, 
                 selectInput("selected_layer", "Choose Shapefile:", 
                             choices = names(shapefile_list), 
                             selected = "Household Waste Collection Region"),
                 
                 tags$style(
                   HTML(".description-text { margin-top: 15px; font-size: 16px; }")
                 ),
                 
                 p(class = "description-text", 
                   "Shapefiles were collected from various resources for the purpose of organic waste mapping in Montreal.")
               ),
               
               mainPanel(
                 width = 9, 
                 leafletOutput("map", height = "90vh")
               )
             ),
             
             absolutePanel(
               bottom = 10, left = 10, 
               div(tags$img(src = "combined.png", style = "max-width: 25vw; height: auto;"))
             )
    ),
    
    # Updated Feature Space tab
    tabPanel("Feature Space",
             sidebarLayout(
               sidebarPanel(
                 width = 2, 
                 selectInput("selected_variable", "Select Variable:", 
                             choices = c("Men's Median Income" = "C2_COUNT_MEN.",
                                         "Women's Median Income" = "C3_COUNT_WOMEN."),
                             selected = "C2_COUNT_MEN.")
               ),
               mainPanel(
                 fluidRow(
                   column(8, leafletOutput("feature_map", height = "85vh", width = "100%")),
                   column(4, plotlyOutput("histogram_plot", height = "85vh", width = "150%"))
                 )
               )
             )
    ),
    
    tabPanel("References",
             fluidRow(
               column(12,
                      h3("References"),
                      tags$ul(
                        tags$li(HTML('<a href="https://www12.statcan.gc.ca/census-recensement/index-eng.cfm?MM=1" target="_blank">Census of Population – Statistics Canada</a>')),
                        tags$li(HTML('<a href="https://www.recyc-quebec.gouv.qc.ca/municipalites/mieux-gerer/plan-gestion-matieres-residuelles/" target="_blank">Plans de gestion des matières résiduelles – RECYC-QUÉBEC</a>')),
                        tags$li(HTML('<a href="https://donnees.montreal.ca/dataset/info-collectes" target="_blank">Secteurs Info-collectes – Données Ouvertes Montréal</a>'))
                      )
               )
             )
    )
  )
)

server <- function(input, output, session) {
  
  # Load and filter dataset
  dat <- read.csv("data/dat_mont_med_emp.csv")
  dat_mont_med_emp <- dat %>% filter(is.finite(C2_COUNT_MEN.), is.finite(C3_COUNT_WOMEN.))
  
  # Prepare data for histogram
  dat_long <- dat_mont_med_emp %>%
    select(C2_COUNT_MEN., C3_COUNT_WOMEN.) %>%
    pivot_longer(cols = everything(), names_to = "Group", values_to = "Count")
  
  # Generate the histogram plot (unchanged)
  output$histogram_plot <- renderPlotly({
    p <- ggplot(dat_long, aes(x = Count, fill = Group)) +
      geom_histogram(alpha = 0.7, bins = 30, color = "black") +
      scale_fill_manual(values = c("blue", "red")) +
      facet_wrap(~ Group, scales = "free", ncol = 1) +
      labs(title = "Median employment income in 2020 for full-year full-time workers in 2020 ($)", 
           x = "Median employment income", y = "Frequency") +
      theme_minimal() +
      theme(legend.position = "none")
    
    ggplotly(p)
  })
  
  # Merge with shapefile data
  shape_data6_wgs84 <- shape_data6_wgs84 %>%
    left_join(dat_mont_med_emp, by = "DGUID")
  
  # Determine shared scale range
  all_values <- c(shape_data6_wgs84$C2_COUNT_MEN., shape_data6_wgs84$C3_COUNT_WOMEN.)
  bins <- pretty(range(all_values, na.rm = TRUE), n = 10)
  color_palette <- colorBin("YlOrRd", domain = all_values, bins = bins, na.color = "gray")
  
  # Render Feature Space Map
  output$feature_map <- renderLeaflet({
    leaflet() %>%
      addTiles() %>%
      setView(lng = -73.7, lat = 45.56, zoom = 10)
  })
  
  observeEvent(input$selected_variable, {
    selected_col <- input$selected_variable
    
    leafletProxy("feature_map") %>%
      clearShapes() %>%
      addPolygons(
        data = shape_data6_wgs84,
        fillColor = ~color_palette(shape_data6_wgs84[[selected_col]]),
        color = "black", weight = 1, opacity = 0.7,
        popup = ~paste0("DGUID: ", DGUID, "<br>", selected_col, ": ", shape_data6_wgs84[[selected_col]]),
        fillOpacity = 0.7
      ) %>%
      clearControls() %>%
      addLegend("bottomright", pal = color_palette, values = all_values,
                title = "Income ($)", opacity = 1)
  })
  
  # Render main map (unchanged)
  output$map <- renderLeaflet({
    leaflet() %>%
      addTiles() %>%
      setView(lng = -73.7, lat = 45.56, zoom = 11)
  })
  
  observeEvent(input$selected_layer, {
    shape_data <- shapefile_list[[input$selected_layer]]
    
    popup_content <- switch(input$selected_layer,
                            "Household Waste Collection Region" = ~paste0("ID: ", ID),
                            "Food Waste Collection Region" = ~paste0("ID: ", ID),
                            "Montreal Administrative Boundaries" = ~paste0("NOM: ", NOM),
                            "Montreal Dissemination Areas" = ~paste0("DGUID: ", DGUID),
                            "Montreal Economic Region" = ~paste0("DGUID: ", DGUID),
                            "Montreal Aggregated Dissemination Areas" = ~paste0("DGUID: ", DGUID)
    )
    
    leafletProxy("map") %>%
      clearShapes() %>%
      addPolygons(
        data = shape_data,
        fillColor = "blue", color = "black", weight = 1, opacity = 0.7,
        popup = popup_content
      )
  })
}

shinyApp(ui, server)
