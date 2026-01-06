import streamlit as st
import pandas as pd
from models import database

def show():
    st.subheader("⚠️ Produits en Alerte de Stock")
    
    # =======================
    # CSS personnalisé - Design Premium
    # =======================
    st.markdown("""
    <style>
    .alert-card {
        background: white;
        border: 1px solid #FEE2E2;
        padding: 0;
        border-radius: 16px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(220, 38, 38, 0.1), 0 2px 4px -1px rgba(220, 38, 38, 0.06);
        transition: all 0.3s ease;
        overflow: hidden;
        position: relative;
    }
    
    .alert-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 6px;
        height: 100%;
        background: linear-gradient(to bottom, #EF4444, #991B1B);
    }
    
    .alert-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 10px 15px -3px rgba(220, 38, 38, 0.15), 0 4px 6px -2px rgba(220, 38, 38, 0.1);
    }
    
    .card-content {
        padding: 20px;
    }
    
    .alert-title {
        color: #1F2937;
        font-weight: 700;
        font-size: 1.25em;
        margin-bottom: 4px;
        font-family: 'Segoe UI', system-ui, sans-serif;
    }
    
    .alert-ref {
        color: #6B7280;
        font-size: 0.85em;
        font-weight: 500;
        letter-spacing: 0.025em;
        margin-bottom: 16px;
        display: block;
    }
    
    .stock-pill {
        background-color: #FEF2F2;
        color: #991B1B;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85em;
        font-weight: 600;
        border: 1px solid #FECACA;
        display: inline-block;
    }
    
    .progress-bg {
        background-color: #F3F4F6;
        height: 8px;
        border-radius: 4px;
        margin: 16px 0;
        overflow: hidden;
    }
    
    .progress-bar {
        background: linear-gradient(90deg, #EF4444, #DC2626);
        height: 100%;
        border-radius: 4px;
        transition: width 1s ease-in-out;
    }
    
    .card-footer {
        background-color: #F9FAFB;
        padding: 12px 20px;
        border-top: 1px solid #F3F4F6;
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 0.9em;
    }
    
    .footer-item {
        display: flex;
        flex-direction: column;
    }
    
    .footer-label {
        font-size: 0.75em;
        color: #6B7280;
        text-transform: uppercase;
        font-weight: 600;
        letter-spacing: 0.05em;
    }
    
    .footer-value {
        color: #374151;
        font-weight: 600;
        margin-top: 2px;
    }
    </style>
    """, unsafe_allow_html=True)

    # Récupérer les produits en alerte
    produits_alerte = database.get_produits_en_alerte()
    
    if produits_alerte:
        # Afficher les statistiques rapides
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("⚠️ Produits en alerte", len(produits_alerte))
        with col2:
            total_manquant = sum(max(0, p['seuil_min'] - p['quantite']) for p in produits_alerte)
            st.metric("📦 Unités manquantes", total_manquant)
        with col3:
            valeur_estimee = sum(p['quantite'] * p['prix_achat'] for p in produits_alerte)
            st.metric("💰 Valeur stock critique", f"{valeur_estimee:,.0f} DH")
        
        st.markdown("---")
        
        # Affichage en grille (Cards)
        cols_per_row = 3
        
        for i in range(0, len(produits_alerte), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, p in enumerate(produits_alerte[i:i+cols_per_row]):
                with cols[j]:
                    # Calcul de pourcentage pour la barre de progression (visuelle)
                    # Si stock = 0, pct = 0. Si stock = seuil, pct = 100 (mais ici on est sûr que stock <= seuil)
                    pct = int((p['quantite'] / p['seuil_min']) * 100) if p['seuil_min'] > 0 else 0
                    
                    # Déterminer le statut et la couleur
                    if p['quantite'] == 0:
                        status_text = "🚫 RUPTURE"
                        status_color = "#991B1B" # Rouge foncé
                    else:
                        status_text = "⚠️ Stock Faible"
                        status_color = "#B91C1C" # Rouge 
                    
                    st.markdown(f"""
<div class="alert-card">
<div class="card-content">
<div style="display: flex; justify-content: space-between; align-items: start;">
<div class="alert-title">{p['nom']}</div>
<span class="stock-pill">{p['quantite']} unités</span>
</div>
<span class="alert-ref">REF: {p['reference']}</span>
<div style="display: flex; justify-content: space-between; font-size: 0.85em; margin-bottom: 4px;">
<span style="color: {status_color}; font-weight: 600;">{status_text}</span>
<span style="color: #6B7280;">Seuil: {p['seuil_min']}</span>
</div>
<div class="progress-bg">
<div class="progress-bar" style="width: {pct}%;"></div>
</div>
</div>
<div class="card-footer">
<div class="footer-item">
<span class="footer-label">Fournisseur</span>
<span class="footer-value">{p.get('fournisseur_nom', '—')}</span>
</div>
<div class="footer-item" style="align-items: flex-end;">
<span class="footer-label">Prix Achat</span>
<span class="footer-value">{p['prix_achat']:,.2f} DH</span>
</div>
</div>
</div>
""", unsafe_allow_html=True)

        st.markdown("---")
        # Bouton global
        if st.button("Aller à l'inventaire pour régulariser", use_container_width=True):
            st.session_state.navigate_to = "📊 Inventaire & Stock"
            st.rerun()

    else:
        st.success("✅ Aucun produit en alerte. Tout le stock est suffisant !")
        st.balloons()
