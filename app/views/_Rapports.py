# app/pages/_Rapports.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from models import database

# =======================
# CSS personnalisé
# =======================
def show():
    st.markdown("""
    <style>
    /* Remove default Streamlit top padding */
    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 0rem !important;
    }
    
    .rapport-header {
        color: #1E40AF;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 5px;
    }
    .kpi-card {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

    st.title("📈 Rapports & Analyses")

    # =======================
    # FILTRES
    # =======================
    with st.sidebar:
        st.header("🔍 Filtres")
        
        # Filtre Date
        date_debut = st.date_input("Date début", value=datetime.today() - timedelta(days=30))
        date_fin = st.date_input("Date fin", value=datetime.today())
        
        # Filtre Type
        type_mvt = st.selectbox("Type de mouvement", ["Tous", "Entrée", "Sortie"])
        
        # Filtre Produit
        all_products = database.get_all_produits()
        produit_options = ["Tous"] + [f"{p['nom']} ({p['reference']})" for p in all_products]
        selected_prod_label = st.selectbox("Produit", produit_options)
        
        selected_prod_id = None
        if selected_prod_label != "Tous":
            # Extraire l'ID du produit sélectionné (un peu hacky via le nom, mais ça marche pour la démo)
            # Idéalement on map le label -> ID
            # Ici on va chercher l'objet correspondant dans la liste
            for p in all_products:
                if f"{p['nom']} ({p['reference']})" == selected_prod_label:
                    selected_prod_id = p['id']
                    break

    # Préparer les filtres pour la requête
    filters = {
        'date_debut': date_debut,
        'date_fin': date_fin,
        'type_mouvement': type_mvt if type_mvt != "Tous" else None,
        'produit_id': selected_prod_id
    }

    # Récupérer les données
    mouvements = database.get_mouvements(filtres=filters)
    df_mvt = pd.DataFrame(mouvements)

    # Onglets
    tab1, tab2 = st.tabs(["📝 Historique Détaillé", "📊 Analyse Graphique"])

    # =======================
    # TAB 1: HISTORIQUE
    # =======================
    with tab1:
        st.markdown(f"<div class='rapport-header'>Historique des Mouvements ({len(df_mvt)})</div>", unsafe_allow_html=True)
        
        if not df_mvt.empty:
            # Nettoyage et formatage pour l'affichage
            df_display = df_mvt[['date_mouvement', 'produit_nom', 'type', 'quantite', 'motif', 'categorie_nom']].copy()
            df_display.columns = ['Date', 'Produit', 'Type', 'Quantité', 'Motif', 'Catégorie']
            
            # Formattage conditionnel (Streamlit le fait nativement un peu, mais on peut personnaliser)
            st.dataframe(
                df_display, 
                use_container_width=True,
                column_config={
                    "Date": st.column_config.DatetimeColumn("Date", format="DD/MM/YYYY HH:mm"),
                }
            )
            
            # Export CSV
            csv = df_display.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Télécharger l'historique (CSV)",
                data=csv,
                file_name=f"rapport_stock_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
            )
        else:
            st.info("Aucun mouvement trouvé pour ces filtres.")

    # =======================
    # TAB 2: ANALYSE
    # =======================
    with tab2:
        st.markdown("<div class='rapport-header'>Analyse des Flux</div>", unsafe_allow_html=True)
        
        if not df_mvt.empty:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("Entrées vs Sorties")
                # Group by Type
                type_counts = df_mvt['type'].value_counts()
                fig_pie = px.pie(
                    values=type_counts.values,
                    names=type_counts.index,
                    color_discrete_map={'entree':'#10B981', 'sortie':'#EF4444'}
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.subheader("Top Produits (Volume)")
                # Group by Product
                prod_gb = df_mvt.groupby('produit_nom')['quantite'].sum().nlargest(10).sort_values()
                fig_bar = px.bar(
                    x=prod_gb.values,
                    y=prod_gb.index,
                    orientation='h',
                    labels={'x': 'Volume Total', 'y': 'Produit'}
                )
                st.plotly_chart(fig_bar, use_container_width=True)

            st.subheader("Évolution Temporelle")
            # Convertir date en datetime si ce n'est pas le cas
            df_mvt['date_mouvement'] = pd.to_datetime(df_mvt['date_mouvement'])
            # Resample par jour
            daily_mvt = df_mvt.set_index('date_mouvement').resample('D')['quantite'].sum().reset_index()
            
            fig_line = px.line(
                daily_mvt, 
                x='date_mouvement', 
                y='quantite',
                markers=True,
                title="Volume total journalier"
            )
            st.plotly_chart(fig_line, use_container_width=True)
            
        else:
            st.info("Données insuffisantes pour l'analyse.")
