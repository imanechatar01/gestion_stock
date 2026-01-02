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
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Produits par Catégorie")
        produits = database.get_produits_dataframe()
        
        if not produits.empty and 'categorie_nom' in produits.columns:
            categories = produits['categorie_nom'].value_counts()
            
            fig = px.pie(
                values=categories.values,
                names=categories.index,
                title="Répartition par catégorie"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun produit enregistré")
    
    with col2:
        st.subheader("📋 Produits à Réapprovisionner")
        
        produits_alerte = database.get_produits_en_alerte()
        
        if produits_alerte:
            for produit in produits_alerte:
                with st.container():
                    col_a, col_b = st.columns([3, 1])
                    
                    with col_a:
                        st.write(f"**{produit['nom']}**")
                        st.caption(f"{produit['categorie_nom']}")
                    
                    with col_b:
                        st.metric(
                            label="Stock", 
                            value=produit['quantite'],
                            delta=f"Seuil: {produit['seuil_min']}"
                        )
        else:
            st.success("✅ Tous les produits ont un stock suffisant")
    
    # Actions rapides
    st.markdown("---")
    st.subheader("🚀 Actions Rapides")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("➕ Ajouter un produit", use_container_width=True):
            st.success("Redirection vers la page Produits")
    
    with col2:
        if st.button("📥 Entrée de stock", use_container_width=True):
            st.success("Redirection vers la page Inventaire")
    
    with col3:
        if st.button("📤 Sortie de stock", use_container_width=True):
            st.success("Redirection vers la page Inventaire")