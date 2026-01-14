# app/pages/_Parameters.py
import streamlit as st
import pandas as pd
import os
from models import database

# =======================
# CSS personnalisé
# =======================
def show():
    # CSS Premium pour la page Catégories
    st.markdown("""
    <style>
    .cat-header {
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 100%);
        padding: 2rem;
        border-radius: 16px;
        color: white;
        margin-bottom: 2rem;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    .cat-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 5px solid;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        margin-bottom: 1rem;
        transition: all 0.3s ease;
    }
    .cat-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 15px rgba(0,0,0,0.1);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 45px;
        white-space: pre-line;
        background-color: #f1f5f9;
        border-radius: 8px;
        color: #475569;
        font-weight: 600;
        border: none;
        padding: 10px 20px;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2563eb !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Header Stylisé
    st.markdown("""
        <div class="cat-header">
            <h1 style="margin:0; color:white; font-size:2rem;">CATEGORIE</h1>
            <p style="margin:0; opacity:0.8;">Architecture et Maintenance des Données</p>
        </div>
    """, unsafe_allow_html=True)

    # Onglets modernisés
    tab1, tab2, tab3 = st.tabs(["Structure des Catégories", "Maintenance Système", "Système"])

    # TAB 1: GESTION DES CATÉGORIES
    with tab1:
        col_form, col_list = st.columns([1, 2])
        
        with col_form:
            st.markdown("#### Nouvelle Catégorie")
            with st.form("add_category", clear_on_submit=True):
                new_cat_name = st.text_input("Dénomination")
                new_cat_color = st.color_picker("Couleur Identitaire", "#3B82F6")
                
                st.markdown("<br>", unsafe_allow_html=True)
                submitted = st.form_submit_button("Enregistrer la catégorie", use_container_width=True)
                
                if submitted:
                    if new_cat_name:
                        try:
                            cats = database.get_all_categories()
                            if any(c['nom'].lower() == new_cat_name.lower() for c in cats):
                                st.error("Dénomination déjà existante.")
                            else:
                                database.add_categorie(new_cat_name, new_cat_color)
                                st.success(f"'{new_cat_name}' enregistrée")
                                time.sleep(1)
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur système: {e}")
                    else:
                        st.warning("Dénomination requise.")

        with col_list:
            st.markdown("#### Répertoire des Catégories")
            categories = database.get_all_categories()
            
            if categories:
                # Récupérer les nombres de produits par catégorie
                prod_counts = {}
                try:
                    df_p = database.get_produits_dataframe()
                    if not df_p.empty:
                        prod_counts = df_p['categorie_nom'].value_counts().to_dict()
                except: pass

                for cat in categories:
                    count = prod_counts.get(cat['nom'], 0)
                    
                    c_main, c_del = st.columns([5, 1])
                    with c_main:
                        st.markdown(f"""
                            <div class="cat-card" style="border-left-color: {cat['couleur']};">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <h4 style="margin:0; color:#1e293b;">{cat['nom']}</h4>
                                        <span style="font-size:0.8rem; color:#64748b;">{count} produit(s) lié(s)</span>
                                    </div>
                                    <div style="width: 24px; height: 24px; background: {cat['couleur']}; border-radius: 6px;"></div>
                                </div>
                            </div>
                        """, unsafe_allow_html=True)
                    
                    with c_del:
                        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
                        if st.button("Effacer", key=f"del_{cat['id']}", help="Attention: Supprime aussi les produits associés"):
                            try:
                                database.delete_categorie(cat['id'])
                                st.success("Supprimé")
                                time.sleep(0.5)
                                st.rerun()
                            except Exception as e:
                                st.error("Erreur")
            else:
                st.info("Aucune catégorie configurée.")

    # TAB 2: MAINTENANCE ET EXPORT
    with tab2:
        st.markdown("#### Intégrité et Exportation")
        
        m_col1, m_col2 = st.columns(2)
        
        with m_col1:
            st.markdown("""
                <div style="background:#f8fafc; padding:1.5rem; border-radius:12px; border:1px solid #e2e8f0;">
                    <h5 style="margin-top:0;">Base de données</h5>
                    <p style="font-size:0.9rem; color:#64748b;">Sécurisez vos données en créant un point de restauration immédiat.</p>
                </div>
            """, unsafe_allow_html=True)
            
            if st.button("Générer une sauvegarde .db", use_container_width=True):
                try:
                    path = database.backup_database()
                    st.success("Point de sauvegarde créé")
                    st.caption(f"Localisation: {path}")
                except Exception as e:
                    st.error(f"Échec: {e}")

        with m_col2:
            st.markdown("""
                <div style="background:#f8fafc; padding:1.5rem; border-radius:12px; border:1px solid #e2e8f0;">
                    <h5 style="margin-top:0;">Exportation Analytique</h5>
                    <p style="font-size:0.9rem; color:#64748b;">Extrayez vos données vers un format tableur standard (CSV).</p>
                </div>
            """, unsafe_allow_html=True)
            
            e_col1, e_col2 = st.columns(2)
            with e_col1:
                if st.button("Export Produits", use_container_width=True):
                    try:
                        f = database.export_to_csv("produits")
                        st.download_button("Télécharger CSV", data=open(f, "rb"), file_name=f, mime="text/csv")
                    except: st.error("Erreur")
            with e_col2:
                if st.button("Export Mouvements", use_container_width=True):
                    try:
                        f = database.export_to_csv("mouvements")
                        st.download_button("Télécharger CSV", data=open(f, "rb"), file_name=f, mime="text/csv")
                    except: st.error("Erreur")

    # TAB 3: À PROPOS
    with tab3:
        st.markdown("""
            <div style="background: white; padding: 2rem; border-radius: 12px; border: 1px solid #e2e8f0;">
                <h4 style="margin-top:0;">StockFlow Pro Framework</h4>
                <p>Système intelligent de gestion et flux logistique.</p>
                <hr>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                    <div>
                        <p style="margin:0; color:#64748b; font-size:0.8rem;">ARCHITECTURE</p>
                        <p style="margin:0; font-weight:600;">Python 3.12 / Streamlit</p>
                    </div>
                    <div>
                        <p style="margin:0; color:#64748b; font-size:0.8rem;">MOTEUR DATA</p>
                        <p style="margin:0; font-weight:600;">SQLite / Pandas</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)
        st.caption("© 2026 - LP SIL Excellence")
