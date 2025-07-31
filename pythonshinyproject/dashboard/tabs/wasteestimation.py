from shiny import ui, render, reactive, App
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.ticker import FuncFormatter

def wasteestimation_tab_ui():
    return ui.page_sidebar(
        ui.sidebar(
            ui.div(
                ui.h3("Waste Data Controls")
            ),
            ui.input_select(
                "selected_year", 
                "Select Year", 
                choices=[""] + [str(yr) for yr in range(2012, 2025)],
                selected=""
            ),
            ui.hr(),
        ),
        ui.card(
            ui.card_header("Generated vs Collected Residual Materials"),
            ui.output_plot("waste_plots", height="1600px"),
            height="auto"
        ),
        title="Waste Estimation",
        fillable=True,
    )


def wasteestimation_tab_server(input, output, session):
    # Load data once at startup
    global waste_data, materials_list
    
    # Initialize global variables
    waste_data = None
    materials_list = []
    
    # Load data directly
    try:
        url = "https://donnees.montreal.ca/dataset/matieres-residuelles-bilan-massique/resource/1341d644-9dd4-4ade-b2b1-9cec53b7beec/download"
        waste_data = pd.read_csv(url)
        
        # Clean numeric columns (columns 4 to 11)
        for col in waste_data.columns[3:11]:
            waste_data[col] = pd.to_numeric(waste_data[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce')
        
        # Montréal agglomeration municipalities
        agglo_mtl_mun = [
            "Ahuntsic-Cartierville", "Anjou", "Côte-des-Neiges–Notre-Dame-de-Grâce",
            "L'Île-Bizard–Sainte-Geneviève", "Lachine", "LaSalle", "Le Plateau-Mont-Royal",
            "Le Sud-Ouest", "Mercier–Hochelaga-Maisonneuve", "Montréal-Nord", "Outremont",
            "Pierrefonds-Roxboro", "Rivière-des-Prairies–Pointe-aux-Trembles",
            "Rosemont–La Petite-Patrie", "Saint-Laurent", "Saint-Léonard", "Verdun",
            "Ville-Marie", "Villeray–Saint-Michel–Parc-Extension",
            "Baie-d'Urfé", "Beaconsfield", "Côte-Saint-Luc", "Dollard-des Ormeaux",
            "Dorval", "Hampstead", "Kirkland", "Montréal-Est", "Montréal-Ouest",
            "Mont-Royal", "Pointe-Claire", "Sainte-Anne-de-Bellevue", "Senneville", "Westmount"
        ]
        
        # Filter to only Montréal agglomeration territories
        waste_data = waste_data[waste_data['territoire'].isin(agglo_mtl_mun)]
        
        # Get all unique materials
        materials_list = sorted(waste_data['matiere'].unique())
        
    except Exception as e:
        print(f"Error loading data: {e}")
    
    @render.plot
    def waste_plots():
        year = input.selected_year()
        
        # Create a large figure for all 8 plots
        fig = plt.figure(figsize=(20, 24))
        
        # If no year selected, show message
        if not year:
            fig.text(0.5, 0.5, "Please select a year to view waste data", 
                    ha='center', va='center', fontsize=20)
            return fig
            
        if waste_data is None or len(materials_list) == 0:
            fig.text(0.5, 0.5, "Error loading data", 
                    ha='center', va='center', fontsize=20)
            return fig
        
        # Filter data for the selected year
        year_data = waste_data[waste_data['annee'] == int(year)]
        
        if year_data.empty:
            fig.text(0.5, 0.5, f"No data available for year {year}", 
                    ha='center', va='center', fontsize=20)
            return fig
        
        # Create a 4x2 grid of subplots explicitly
        axes = fig.subplots(4, 2, squeeze=False)
        
        # Divide materials into exactly 8 groups
        n_materials = len(materials_list)
        materials_per_group = n_materials // 8
        if materials_per_group < 1:
            materials_per_group = 1
        
        # Create exactly 8 groups, some may be empty if not enough materials
        material_groups = []
        for i in range(8):
            start_idx = i * materials_per_group
            end_idx = (i + 1) * materials_per_group if i < 7 else n_materials
            if start_idx < n_materials:
                group = materials_list[start_idx:end_idx]
                material_groups.append(group)
            else:
                material_groups.append([])  # Empty group
        
        # Ensure we have exactly 8 groups
        while len(material_groups) < 8:
            material_groups.append([])
        
        # Debug print for materials per group
        print(f"Materials list length: {n_materials}")
        for i, group in enumerate(material_groups):
            print(f"Group {i+1}: {len(group)} materials - {group}")
        
        # Process each group and create a subplot
        for i in range(8):
            row = i // 2
            col = i % 2
            ax = axes[row, col]
            
            materials = material_groups[i] if i < len(material_groups) else []
            
            # If no materials in this group, show a placeholder
            if not materials:
                ax.text(0.5, 0.5, f"Group {i+1}: No materials to display", 
                        ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f"Group {i+1}")
                continue
            
            # Filter data for these materials
            df_group = year_data[year_data['matiere'].isin(materials)]
            
            if df_group.empty:
                ax.text(0.5, 0.5, f"No data for materials in group {i+1}", 
                        ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f"Materials: {', '.join(materials)}")
                continue
            
            # Create a DF for plotting
            plot_data = []
            for material in materials:
                material_data = df_group[df_group['matiere'] == material]
                
                for _, row in material_data.iterrows():
                    plot_data.append({
                        'material': material,
                        'territory': row['territoire'],
                        'generated': row['quantite_generee_donnees_agglo'],
                        'collected': row['quantite_collectee_donnees_agglo']
                    })
            
            plot_df = pd.DataFrame(plot_data)
            
            if plot_df.empty:
                ax.text(0.5, 0.5, "No data to display", 
                        ha='center', va='center', transform=ax.transAxes)
                ax.set_title(f"Materials: {', '.join(materials)}")
                continue
            
            # Group by material for plotting
            material_groups_plot = plot_df.groupby('material')
            
            # Plot each material separately
            for material_name, material_group in material_groups_plot:
                # For each territory, create grouped bars
                grouped = material_group.groupby('territory').agg({
                    'generated': 'mean',
                    'collected': 'mean'
                }).reset_index()
                
                # Sort by total waste
                grouped['total'] = grouped['generated'] + grouped['collected']
                grouped = grouped.sort_values('total')
                
                # Plot bars
                x = np.arange(len(grouped))
                width = 0.35
                
                # Generate bars for collected and generated
                ax.bar(x - width/2, grouped['generated'], width, label='Generated' if i == 0 else "", color='#E69F00')
                ax.bar(x + width/2, grouped['collected'], width, label='Collected' if i == 0 else "", color='#56B4E9')
                
                # Set x-tick labels
                ax.set_xticks(x)
                ax.set_xticklabels(grouped['territory'], rotation=45, ha='right', fontsize=6)
                
                # Set title and labels
                ax.set_title(f"Material: {material_name}")
                ax.set_ylabel('Quantity (tonnes)')
                
                # Add grid lines
                ax.grid(True, axis='y', linestyle='--', alpha=0.7)
                
                # Format y-axis with thousands separator
                ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: format(int(x), ',')))
            
            # Only show legend on first plot
            if i == 0:
                ax.legend()
        
        # Add overall title
        fig.suptitle(f"Generated vs Collected Residual Materials by Territory ({year})", fontsize=16)
        
        # Adjust layout
        plt.tight_layout(rect=[0, 0, 1, 0.97])  # Leave room for suptitle
        
        return fig