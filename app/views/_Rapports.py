# app/pages/_Rapports.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
from models import database
from services.pdf_service import generate_stock_report

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
        
        st.markdown("---")
        st.header("📄 Export Rapport PDF")
        periode_export = st.selectbox(
            "Période du rapport PDF", 
            ["Cette Semaine", "Ce Mois", "Cette Année"],
            key="pdf_period_selector"
        )
        
        # Si le sélecteur change, on réinitialise le rapport prêt
        if "last_pdf_period" not in st.session_state:
            st.session_state.last_pdf_period = periode_export
            
        if st.session_state.last_pdf_period != periode_export:
            if 'pdf_report' in st.session_state:
                del st.session_state.pdf_report
            st.session_state.last_pdf_period = periode_export
        
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
                use_container_width=True
            )
            
            # --- PDF Export Logic ---
            st.markdown("---")
            if st.button("📑 Préparer le Rapport PDF Général", use_container_width=True):
                with st.spinner("Génération du PDF en cours..."):
                    # Calculer les dates selon la période choisie
                    fin = datetime.now()
                    if periode_export == "Cette Semaine":
                        debut = fin - timedelta(days=fin.weekday())
                        debut = debut.replace(hour=0, minute=0, second=0, microsecond=0)
                    elif periode_export == "Ce Mois":
                        debut = fin.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    else: # Cette Année
                        debut = fin.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                    
                    # Récupérer les données pour le PDF
                    pdf_filters = {'date_debut': debut.date(), 'date_fin': fin.date()}
                    stats_global = database.get_statistiques()
                    period_mvt = database.get_mouvements(filtres=pdf_filters)
                    
                    # Stocker dans le state
                    st.session_state.pdf_report = generate_stock_report(stats_global, period_mvt, f"Général ({periode_export})")
                    st.session_state.pdf_filename = f"rapport_stock_{periode_export.lower().replace(' ', '_')}_{fin.strftime('%Y%m%d')}.pdf"
            
            # Afficher le bouton de téléchargement si le rapport est prêt
            if 'pdf_report' in st.session_state:
                st.success("✅ Rapport PDF prêt !")
                st.download_button(
                    label="⬇️ Télécharger le Rapport PDF",
                    data=st.session_state.pdf_report,
                    file_name=st.session_state.pdf_filename,
                    mime="application/pdf",
                    use_container_width=True
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
