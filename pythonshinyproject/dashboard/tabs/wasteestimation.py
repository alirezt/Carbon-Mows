from shiny import ui, render, reactive, App
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import matplotlib.style as style

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
            ui.output_plot("waste_plots", height="1800px"),
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
        
        # Create figure with clean styling
        plt.style.use('default')  # Start with clean default style
        fig, axs = plt.subplots(4, 2, figsize=(20, 28))
        fig.patch.set_facecolor('white')
        
        # If no year selected, show message
        if not year:
            fig.text(0.5, 0.5, "Please select a year to view waste data", 
                    ha='center', va='center', fontsize=18, color='#666666')
            for ax in axs.flat:
                ax.set_visible(False)
            return fig
            
        if waste_data is None or len(materials_list) == 0:
            fig.text(0.5, 0.5, "Error loading data", 
                    ha='center', va='center', fontsize=18, color='#666666')
            for ax in axs.flat:
                ax.set_visible(False)
            return fig
        
        # Filter data for the selected year
        year_data = waste_data[waste_data['annee'] == int(year)]
        
        if year_data.empty:
            fig.text(0.5, 0.5, f"No data available for year {year}", 
                    ha='center', va='center', fontsize=18, color='#666666')
            for ax in axs.flat:
                ax.set_visible(False)
            return fig
        
        # Divide materials into exactly 8 groups
        n_materials = len(materials_list)
        materials_per_group = n_materials // 8
        if materials_per_group < 1:
            materials_per_group = 1
        
        material_groups = []
        for i in range(8):
            start_idx = i * materials_per_group
            end_idx = (i + 1) * materials_per_group if i < 7 else n_materials
            if start_idx < n_materials:
                group = materials_list[start_idx:end_idx]
                material_groups.append(group)
            else:
                material_groups.append([])
        
        while len(material_groups) < 8:
            material_groups.append([])
        
        # Beautiful color palette
        colors = {
            'Generated': '#FF6B35',  # Modern orange
            'Collected': '#4A90E2'   # Modern blue
        }
        
        # Process each group and create a subplot
        for i in range(8):
            row = i // 2
            col = i % 2
            ax = axs[row, col]
            
            # Clean subplot styling
            ax.set_facecolor('#fafafa')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.spines['left'].set_color('#cccccc')
            ax.spines['bottom'].set_color('#cccccc')
            
            materials = material_groups[i] if i < len(material_groups) else []
            
            if not materials:
                ax.text(0.5, 0.5, f"No materials in group {i+1}", 
                        ha='center', va='center', transform=ax.transAxes, 
                        fontsize=12, color='#888888')
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_title(f"Group {i+1}", fontsize=14, pad=20, color='#333333')
                continue
            
            # Filter data for these materials
            df_group = year_data[year_data['matiere'].isin(materials)]
            
            if df_group.empty:
                ax.text(0.5, 0.5, "No data available", 
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=12, color='#888888')
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_title(', '.join(materials), fontsize=14, pad=20, color='#333333')
                continue
            
            # Create plotting data
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
                continue
            
            # Aggregate and sort data
            grouped = plot_df.groupby('territory').agg({
                'generated': 'mean',
                'collected': 'mean'
            }).reset_index()
            
            grouped['total'] = grouped['generated'] + grouped['collected']
            grouped = grouped.sort_values('total')
            
            # Create beautiful bars
            x = np.arange(len(grouped))
            width = 0.35
            
            bars1 = ax.bar(x - width/2, grouped['generated'], width, 
                          label='Generated' if i == 0 else "", 
                          color=colors['Generated'], alpha=0.8, edgecolor='white', linewidth=0.5)
            bars2 = ax.bar(x + width/2, grouped['collected'], width, 
                          label='Collected' if i == 0 else "", 
                          color=colors['Collected'], alpha=0.8, edgecolor='white', linewidth=0.5)
            
            # Clean axis formatting
            ax.set_xticks(x)
            ax.set_xticklabels([t[:12] + '...' if len(t) > 15 else t for t in grouped['territory']], 
                              rotation=45, ha='right', fontsize=9, color='#555555')
            
            # Format y-axis
            ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{int(x/1000)}K' if x >= 1000 else f'{int(x)}'))
            ax.tick_params(axis='y', labelsize=9, colors='#555555')
            
            # Clean title
            material_title = ', '.join([m[:20] + '...' if len(m) > 23 else m for m in materials])
            ax.set_title(material_title, fontsize=12, pad=20, color='#333333', weight='bold')
            ax.set_ylabel('Quantity (tonnes)', fontsize=10, color='#555555')
            
            # Light grid
            ax.grid(True, axis='y', linestyle='--', alpha=0.3, color='#cccccc')
            
            # Legend only on first plot
            if i == 0:
                ax.legend(loc='upper right', frameon=False, fontsize=10)
        
        # Clean overall title
        fig.suptitle(f"Generated vs Collected Residual Materials by Territory ({year})", 
                    fontsize=18, y=0.98, color='#333333', weight='bold')
        
        # Perfect spacing
        plt.subplots_adjust(
            left=0.08,
            bottom=0.06,
            right=0.95,
            top=0.92,
            wspace=0.3,
            hspace=0.5
        )
        
        return fig