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
            ui.input_selectize(
                "selected_year", 
                "Select Year", 
                choices=[""] + [str(yr) for yr in range(2012, 2025)],
                selected=""
            ),
            ui.hr(),
            ui.input_selectize(
                "selected_waste_types", 
                "Select Waste Type", 
                choices=[
                    "",
                    "Matières recyclables",
                    "Matières organiques", 
                    "Résidus de construction, rénovation, démolition et encombrants",
                    "Résidus domestiques dangereux",
                    "Textiles",
                    "Autres (produits électroniques)",
                    "Ordures ménagères éliminées",
                    "Résidus de construction, rénovation, démolition et encombrants éliminés",
                    "Résidus domestiques dangereux et PE"
                ],
                selected="",
            ),
            ui.input_selectize(
                "selected_territories",
                "Select Municipalities", 
                choices=[
                    "", "Ahuntsic-Cartierville", "Anjou", "Côte-des-Neiges–Notre-Dame-de-Grâce",
                    "L'Île-Bizard–Sainte-Geneviève", "Lachine", "LaSalle", "Le Plateau-Mont-Royal",
                    "Le Sud-Ouest", "Mercier–Hochelaga-Maisonneuve", "Montréal-Nord", "Outremont",
                    "Pierrefonds-Roxboro", "Rivière-des-Prairies–Pointe-aux-Trembles",
                    "Rosemont–La Petite-Patrie", "Saint-Laurent", "Saint-Léonard", "Verdun",
                    "Ville-Marie", "Villeray–Saint-Michel–Parc-Extension",
                    "Baie-d'Urfé", "Beaconsfield", "Côte-Saint-Luc", "Dollard-des Ormeaux",
                    "Dorval", "Hampstead", "Kirkland", "Montréal-Est", "Montréal-Ouest",
                    "Mont-Royal", "Pointe-Claire", "Sainte-Anne-de-Bellevue", "Senneville", "Westmount"
                ],
                selected="",
            ),
        ),
        ui.card(
            ui.card_header("Generated vs Collected Residual Materials"),
            ui.output_plot("waste_plots", height="1800px"),
            height="auto",
            collapsible=True,
        ),
        ui.card(
            ui.card_header("Time Series Analysis"),
            ui.output_plot("time_series_plot", height="600px"),
            height="auto",
            collapsible=True,
        ),
        title="Waste Estimation",
        fillable=True,
    )


def wasteestimation_tab_server(input, output, session):
    global waste_data, materials_list
    
    waste_data = None
    materials_list = []
    
    try:
        url = "https://donnees.montreal.ca/dataset/matieres-residuelles-bilan-massique/resource/1341d644-9dd4-4ade-b2b1-9cec53b7beec/download"
        waste_data = pd.read_csv(url)
        
        for col in waste_data.columns[3:11]:
            waste_data[col] = pd.to_numeric(waste_data[col].astype(str).str.replace(r'[^0-9.]', '', regex=True), errors='coerce')
        
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
        
        waste_data = waste_data[waste_data['territoire'].isin(agglo_mtl_mun)]
        
        materials_list = sorted(waste_data['matiere'].unique())
        
    except Exception as e:
        print(f"Error loading data: {e}")
    
    @render.plot
    def waste_plots():
        year = input.selected_year()
        
        plt.style.use('default')  
        fig, axs = plt.subplots(4, 2, figsize=(20, 28))
        fig.patch.set_facecolor('white')
        
        if not year:
            fig.text(0.5, 0.5, "Please select a year to view waste data", 
                    ha='center', va='center', fontsize=18, color='#666666')
            for ax in axs.flat:
                ax.set_visible(False)
            return fig
        
        year_data = waste_data[waste_data['annee'] == int(year)]
        
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
        
        colors = {
            'Generated': '#FF6B35',  
            'Collected': '#4A90E2'   
        }
        
        for i in range(8):
            row = i // 2
            col = i % 2
            ax = axs[row, col]
            
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
            
            df_group = year_data[year_data['matiere'].isin(materials)]
            
            if df_group.empty:
                ax.text(0.5, 0.5, "No data available", 
                        ha='center', va='center', transform=ax.transAxes,
                        fontsize=12, color='#888888')
                ax.set_xticks([])
                ax.set_yticks([])
                ax.set_title(', '.join(materials), fontsize=14, pad=20, color='#333333')
                continue
            
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

    @render.plot  
    def time_series_plot():
        waste_type = input.selected_waste_types()
        territory = input.selected_territories()
        
        # Create figure with same styling as first graphs
        plt.style.use('default')
        fig, ax = plt.subplots(1, 1, figsize=(12, 8))
        fig.patch.set_facecolor('white')
        
        # Check if both selections are made
        if not waste_type or not territory:
            fig.text(0.5, 0.5, "Please select both a waste type and a municipality to view time series data", 
                    ha='center', va='center', fontsize=14, color='#666666')
            ax.set_visible(False)
            return fig
            
        if waste_data is None:
            fig.text(0.5, 0.5, "Error loading data", 
                    ha='center', va='center', fontsize=14, color='#666666')
            ax.set_visible(False)
            return fig
        
        # Filter data for selected waste type and territory
        data_filtered = waste_data[
            (waste_data['matiere'] == waste_type) & 
            (waste_data['territoire'] == territory)
        ].copy()
        
        if data_filtered.empty:
            fig.text(0.5, 0.5, f"No data available for {waste_type} in {territory}", 
                    ha='center', va='center', fontsize=14, color='#666666')
            ax.set_visible(False)
            return fig
        
        # Reshape to long format
        data_long = data_filtered.melt(
            id_vars=['annee'], 
            value_vars=['quantite_generee_donnees_agglo', 'quantite_collectee_donnees_agglo'],
            var_name='type', value_name='quantite'
        )
        
        # Recode type
        type_map = {
            'quantite_generee_donnees_agglo': 'Generated',
            'quantite_collectee_donnees_agglo': 'Collected'
        }
        data_long['type'] = data_long['type'].map(type_map)
        
        # Same styling as first graphs
        ax.set_facecolor('#fafafa')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_color('#cccccc')
        ax.spines['bottom'].set_color('#cccccc')
        
        # Same color palette
        colors = {
            'Generated': '#FF6B35',  # Modern orange
            'Collected': '#4A90E2'   # Modern blue
        }
        
        # Create the bars
        generated_data = data_long[data_long['type'] == 'Generated']
        collected_data = data_long[data_long['type'] == 'Collected']
        
        years = sorted(data_long['annee'].unique())
        x = np.arange(len(years))
        width = 0.35
        
        generated_values = [generated_data[generated_data['annee'] == year]['quantite'].iloc[0] if len(generated_data[generated_data['annee'] == year]) > 0 else 0 for year in years]
        collected_values = [collected_data[collected_data['annee'] == year]['quantite'].iloc[0] if len(collected_data[collected_data['annee'] == year]) > 0 else 0 for year in years]
        
        bars1 = ax.bar(x - width/2, generated_values, width, 
                    label='Generated', color=colors['Generated'], 
                    alpha=0.8, edgecolor='white', linewidth=0.5)
        bars2 = ax.bar(x + width/2, collected_values, width, 
                    label='Collected', color=colors['Collected'], 
                    alpha=0.8, edgecolor='white', linewidth=0.5)
        
        # Format axes
        ax.set_xticks(x)
        ax.set_xticklabels(years, rotation=45, ha='right', fontsize=10, color='#555555')
        ax.set_xlabel("Year", fontsize=12, color='#555555')
        ax.set_ylabel("Quantity (tonnes)", fontsize=12, color='#555555')
        
        # Format y-axis with same style
        ax.yaxis.set_major_formatter(FuncFormatter(lambda x, p: f'{int(x/1000)}K' if x >= 1000 else f'{int(x)}'))
        ax.tick_params(axis='y', labelsize=10, colors='#555555')
        
        # Title with same style
        territory_short = territory[:20] + '...' if len(territory) > 23 else territory
        waste_type_short = waste_type[:30] + '...' if len(waste_type) > 33 else waste_type
        ax.set_title(f"Generated vs Collected: {waste_type_short}\nin {territory_short}", 
                    fontsize=14, pad=20, color='#333333', weight='bold')
        
        # Grid and legend with same style
        ax.grid(True, axis='y', linestyle='--', alpha=0.3, color='#cccccc')
        ax.legend(loc='upper right', frameon=False, fontsize=12)
        
        plt.subplots_adjust(
            left=0.1,      # Left margin
            bottom=0.15,   # Bottom margin (increased to prevent x-axis label cutoff)
            right=0.95,    # Right margin
            top=0.85       # Top margin (increased to add space below card header)
        )

        return fig