# app/pages/_dashboard.py - Page Tableau de Bord
import streamlit as st
import pandas as pd
import plotly.express as px
from models import database

def show():
    # CSS Personnalisé pour un look Premium
    st.markdown("""
    <style>
    /* Metric Cards Styling */
    .metric-container {
        display: flex;
        justify-content: space-between;
        gap: 20px;
        margin-bottom: 25px;
    }
    .metric-card {
        background: white;
        border-radius: 12px;
        padding: 20px;
        flex: 1;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        border: 1px solid #f0f0f0;
        transition: transform 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-5px);
    }
    .metric-title {
        color: #64748B;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #1E293B;
        font-size: 24px;
        font-weight: 700;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 18px;
        font-weight: 600;
        color: #1E293B;
        margin: 25px 0 15px 0;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    /* Activity Item Styling */
    .activity-item {
        background: white;
        padding: 12px 15px;
        border-radius: 8px;
        margin-bottom: 8px;
        border-left: 4px solid #3B82F6;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 4px rgba(0,0,0,0.02);
    }
    .activity-entree { border-left-color: #10B981; }
    .activity-sortie { border-left-color: #EF4444; }
    
    </style>
    """, unsafe_allow_html=True)

    # Statistiques
    stats = database.get_statistiques()
    
    # Titre de la page
    st.markdown("<h2 style='color: #1E293B; margin-bottom: 25px;'>Tableau de Bord</h2>", unsafe_allow_html=True)

    # Métriques Premium en HTML
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Produits</div>
            <div class="metric-value">{stats['total_produits']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Valeur Stock</div>
            <div class="metric-value">{stats['valeur_totale']:,.0f} DH</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col3:
        # Couleur rouge si alertes > 0
        alert_color = "#EF4444" if stats['alertes'] > 0 else "#64748B"
        st.markdown(f"""
        <div class="metric-card" style="border-left: 4px solid {alert_color}">
            <div class="metric-title">Alertes Stock</div>
            <div class="metric-value" style="color: {alert_color}">{stats['alertes']}</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Fournisseurs</div>
            <div class="metric-value">{stats['total_fournisseurs']}</div>
        </div>
        """, unsafe_allow_html=True)

    # Section Graphiques
    st.markdown("<div class='section-header'>Analyses Visuelles</div>", unsafe_allow_html=True)
    col_chart1, col_chart2 = st.columns(2)
    
    produits = database.get_produits_dataframe()
    
    with col_chart1:
        if not produits.empty and 'categorie_nom' in produits.columns:
            df_cat = produits.groupby(['categorie_nom', 'categorie_couleur']).size().reset_index(name='count')
            color_map = dict(zip(df_cat['categorie_nom'], df_cat['categorie_couleur']))
            
            fig = px.pie(
                df_cat,
                values='count',
                names='categorie_nom',
                hole=0.5,
                color='categorie_nom',
                color_discrete_map=color_map,
                title="<b>Volume par Catégorie</b>"
            )
            fig.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=350, showlegend=True, legend=dict(orientation="h", y=-0.1))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun produit enregistré")
            
    with col_chart2:
        st.write("") # Petit espacement
        alertes = database.get_produits_en_alerte()
        if alertes:
            df_alertes = pd.DataFrame(alertes)
            # Graphique à barres pour les alertes
            fig_alert = px.bar(
                df_alertes,
                x='quantite',
                y='nom',
                orientation='h',
                title="<b>Stocks Critiques</b>",
                color_discrete_sequence=['#EF4444'], # Rouge alerte
                labels={'quantite': 'En stock', 'nom': ''}
            )
            fig_alert.update_layout(
                margin=dict(t=40, b=0, l=0, r=0), 
                height=350,
                xaxis_title="Unités restantes",
                yaxis={'categoryorder':'total descending'}
            )
            st.plotly_chart(fig_alert, use_container_width=True)
        else:
            st.success("Tous les stocks sont au-dessus du seuil d'alerte !")
            st.markdown("""
            <div style="height: 290px; border: 2px dashed #E2E8F0; border-radius: 12px; display: flex; align-items: center; justify-content: center; color: #94A3B8; flex-direction: column;">
                <p style="margin-top: 10px;">Aucune alerte de stock</p>
            </div>
            """, unsafe_allow_html=True)

    # Activité Récente
    st.markdown("<div class='section-header'>Activité Récente</div>", unsafe_allow_html=True)
    mouvements = database.get_mouvements(filtres={'limit': 3})
    if mouvements:
        for m in mouvements:
            type_class = "activity-entree" if m['type'] == 'entree' else "activity-sortie"
            icon = "" if m['type'] == 'entree' else ""
            st.markdown(f"""
            <div class="activity-item {type_class}">
                <div>
                    <span style="font-weight: 600;">{m['produit_nom']}</span><br>
                    <small style="color: #64748B;">{m['motif'] or 'Mouvement de stock'}</small>
                </div>
                <div style="text-align: right;">
                    <span style="font-weight: 700;">{m['quantite']} unités</span><br>
                    <small style="color: #94A3B8;">{m['date_mouvement']}</small>
                </div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("Aucun mouvement récent.")

    # Actions Rapides en une seule ligne
    st.markdown("<div class='section-header'>Actions Rapides</div>", unsafe_allow_html=True)
    aq1, aq2, aq3, aq4 = st.columns(4)
    
    with aq1:
        st.button("Nouveau Produit", on_click=lambda: st.session_state.update(main_navigation="Gestion Produits"), use_container_width=True)
    with aq2:
        st.button("Faire une Entrée", on_click=lambda: st.session_state.update(main_navigation="Inventaire & Stock", inventory_default_tab="entrees"), use_container_width=True)
    with aq3:
        st.button("Faire une Sortie", on_click=lambda: st.session_state.update(main_navigation="Inventaire & Stock", inventory_default_tab="sorties"), use_container_width=True)
    with aq4:
        st.button("Voir Fournisseurs", on_click=lambda: st.session_state.update(main_navigation="Fournisseurs"), use_container_width=True)
