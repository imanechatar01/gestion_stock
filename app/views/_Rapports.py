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

    st.title("Rapports & Analyses")

    # =======================
    # FILTRES
    # =======================
    with st.sidebar:
        st.header("Filtres")
        
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

    # =======================
    # ZONE D'EXPORT PDF (VISIBLE)
    # =======================
    with st.expander("📄 EXPORTER UN RAPPORT PDF", expanded=True):
        col_p, col_b, col_d = st.columns([2, 1, 1])
        with col_p:
            periode_export = st.selectbox(
                "Période du rapport", 
                [
                    "Cette Semaine (Hebdo)", 
                    "Ce Mois (Mensuel)", 
                    "Cette Année (Annuel)",
                    "Dates filtrées (Personnalisé)"
                ],
                key="pdf_period_selector_main"
            )
            
            # Si le sélecteur change, on réinitialise le rapport prêt
            if "last_pdf_period_main" not in st.session_state:
                st.session_state.last_pdf_period_main = periode_export
                
            if st.session_state.last_pdf_period_main != periode_export:
                if 'pdf_report' in st.session_state:
                    del st.session_state.pdf_report
                st.session_state.last_pdf_period_main = periode_export

        with col_b:
            if st.button("📑 Générer PDF", use_container_width=True, type="primary"):
                with st.spinner("Génération..."):
                    fin_dt = datetime.now()
                    if "Semaine" in periode_export:
                        debut_dt = fin_dt - timedelta(days=fin_dt.weekday())
                        debut_dt = debut_dt.replace(hour=0, minute=0, second=0, microsecond=0)
                        pl = "Hebdomadaire"
                    elif "Mois" in periode_export:
                        debut_dt = fin_dt.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                        pl = "Mensuel"
                    elif "Année" in periode_export:
                        debut_dt = fin_dt.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
                        pl = "Annuel"
                    else: # Personnalisé
                        debut_dt = datetime.combine(date_debut, datetime.min.time())
                        fin_dt = datetime.combine(date_fin, datetime.max.time())
                        pl = f"Personnalisé"
                    
                    pdf_filters = {'date_debut': debut_dt, 'date_fin': fin_dt}
                    stats_p = database.get_statistiques()
                    mvt_p = database.get_mouvements(filtres=pdf_filters)
                    
                    st.session_state.pdf_report = generate_stock_report(stats_p, mvt_p, f"Rapport {pl}")
                    st.session_state.pdf_filename = f"rapport_stock_{pl.lower()}_{datetime.now().strftime('%Y%m%d')}.pdf"
                    st.toast("Rapport généré avec succès !")
        
        with col_d:
            if 'pdf_report' in st.session_state:
                st.download_button(
                    label="⬇️ Télécharger",
                    data=st.session_state.pdf_report,
                    file_name=st.session_state.pdf_filename,
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                st.button("⬇️ Télécharger", disabled=True, use_container_width=True)

    # Onglets
    tab1, tab2 = st.tabs(["Historique Détaillé", "Analyse Graphique"])

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
                "Télécharger l'historique (CSV)",
                data=csv,
                file_name=f"rapport_stock_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
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
                prod_df = prod_gb.reset_index()
                prod_df.columns = ['Produit', 'Volume']
                
                fig_bar = px.bar(
                    prod_df,
                    x='Volume',
                    y='Produit',
                    orientation='h',
                    labels={'Volume': 'Volume Total', 'Produit': 'Produit'}
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
