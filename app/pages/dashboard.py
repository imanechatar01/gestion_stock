# app/pages/_dashboard.py - Page Tableau de Bord
import streamlit as st
import pandas as pd
import plotly.express as px
from models import database

def show():
    st.title("🏠 Tableau de Bord")
    
    # Statistiques
    stats = database.get_statistiques()
    
    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Produits", stats['total_produits'])
    with col2:
        st.metric("💰 Valeur", f"{stats['valeur_totale']:,.0f} €")
    with col3:
        st.metric("⚠️ Alertes", stats['alertes'])
    with col4:
        st.metric("👥 Fournisseurs", stats['total_fournisseurs'])
    
    st.markdown("---")
    
    # Section graphiques
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📊 Nombre de Produits par Catégorie")
        produits = database.get_produits_dataframe()
        
        if not produits.empty and 'categorie_nom' in produits.columns:
            categories = produits['categorie_nom'].value_counts()
            
            fig = px.pie(
                values=categories.values,
                names=categories.index,
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_layout(showlegend=True, legend=dict(orientation="h"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun produit enregistré")
            
    with col_chart2:
        st.subheader("💎 Top 10 Valeur Stock")
        if not produits.empty:
            # Calculer la valeur du stock
            produits['valeur_stock'] = produits['quantite'] * produits['prix_vente']
            top_products = produits.nlargest(10, 'valeur_stock')
            
            fig_bar = px.bar(
                top_products,
                x='valeur_stock',
                y='nom',
                orientation='h',
                text='valeur_stock',
                color='valeur_stock',
                color_continuous_scale='Blues'
            )
            fig_bar.update_layout(yaxis={'categoryorder':'total ascending'}, showlegend=False)
            fig_bar.update_traces(texttemplate='%{text:.0f} €', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Pas assez de données.")

    st.markdown("---")

    # Section Activité Récente et Alertes
    col_activity, col_alerts = st.columns([2, 1])
    
    with col_activity:
        st.subheader("🕒 Activité Récente")
        try:
            mouvements = database.get_mouvements(filtres={'limit': 5})
            if mouvements:
                # Créer un DataFrame simple pour l'affichage
                data = []
                for m in mouvements:
                    icon = "📥" if m['type'] == 'entree' else "📤" if m['type'] == 'sortie' else "📝"
                    data.append({
                        "Type": f"{icon} {m['type'].capitalize()}",
                        "Produit": m['produit_nom'],
                        "Quantité": m['quantite'],
                        "Date": m['date_mouvement'],
                        "Motif": m['motif']
                    })
                st.dataframe(pd.DataFrame(data), hide_index=True, use_container_width=True)
            else:
                st.info("Aucun mouvement récent.")
        except Exception as e:
            st.error(f"Erreur chargement activité: {e}")

    with col_alerts:
        st.subheader("⚠️ Alertes Stock")
        
        produits_alerte = database.get_produits_en_alerte()
        
        if produits_alerte:
            for produit in produits_alerte:
                st.warning(f"**{produit['nom']}** (Qte: {produit['quantite']})")
        else:
            st.success("✅ Stock sain")
    
    # Actions rapides
    st.markdown("---")
    st.subheader("🚀 Accès Rapide")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info("📦 **Gestion Produits**\n\nAjouter ou modifier des produits.")
    
    with col2:
        st.info("📊 **Inventaire**\n\nEntrées et sorties de stock.")
        
    with col3:
        st.info("👥 **Fournisseurs**\n\nGérer vos partenaires.")

    with col4:
        st.info("⚙️ **Paramètres**\n\nBackup et configuration.")