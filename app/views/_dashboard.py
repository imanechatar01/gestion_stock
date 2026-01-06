# app/pages/_dashboard.py - Page Tableau de Bord
import streamlit as st
import pandas as pd
import plotly.express as px
from models import database

def show():

    
    # Statistiques
    stats = database.get_statistiques()
    
    # Métriques
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📦 Produits", stats['total_produits'])
    with col2:
        st.metric("💰 Valeur", f"{stats['valeur_totale']:,.0f} DH")
    with col3:
        st.metric("⚠️ Alertes", stats['alertes'])
    with col4:
        st.metric("👥 Fournisseurs", stats['total_fournisseurs'])
    
    st.markdown("---")
    
    # Section graphiques
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.subheader("📊 Répartition par Catégorie")
        produits = database.get_produits_dataframe()
        
        if not produits.empty and 'categorie_nom' in produits.columns:
            # Préparer les données avec les couleurs
            df_cat = produits.groupby(['categorie_nom', 'categorie_couleur']).size().reset_index(name='count')
            
            # Créer le mapping de couleurs {Nom: Couleur}
            color_map = dict(zip(df_cat['categorie_nom'], df_cat['categorie_couleur']))
            
            fig = px.pie(
                df_cat,
                values='count',
                names='categorie_nom',
                title="Répartition par catégorie",
                hole=0.4,
                color='categorie_nom',
                color_discrete_map=color_map
            )
            fig.update_layout(showlegend=True, legend=dict(orientation="h"))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucun produit enregistré")
            
    with col_chart2:
        st.subheader("💎 Top 10 Valeur Stock")
        if not produits.empty and 'quantite' in produits.columns and 'prix_vente' in produits.columns:
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
            fig_bar.update_traces(texttemplate='%{text:.0f} DH', textposition='outside')
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("Pas assez de données.")

    st.markdown("---")

    # Section Activité Récente et Alertes
    # Section Activité Récente
    st.subheader("🕒 Activité Récente")
    try:
        mouvements = database.get_mouvements(filtres={'limit': 10}) # Increased limit slightly since it has more space
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
    
    # Actions rapides
    st.markdown("---")
    st.subheader("🚀 Actions Rapides")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.button("➕ Ajouter un produit", on_click=lambda: st.session_state.update(main_navigation="📦 Gestion Produits"), use_container_width=True)

    with col2:
        st.button("📥 Entrée de stock", on_click=lambda: st.session_state.update(main_navigation="📊 Inventaire & Stock", inventory_default_tab="entrees"), use_container_width=True)
    
    with col3:
        st.button("📤 Sortie de stock", on_click=lambda: st.session_state.update(main_navigation="📊 Inventaire & Stock", inventory_default_tab="sorties"), use_container_width=True)
            
    with col4:
        st.button("👥 Fournisseurs", on_click=lambda: st.session_state.update(main_navigation="👥 Fournisseurs"), use_container_width=True)