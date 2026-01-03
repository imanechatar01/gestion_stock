# app/pages/_Parameters.py
import streamlit as st
import pandas as pd
import os
from models import database

# =======================
# CSS personnalisé
# =======================
def show():
    st.markdown("""
    <style>
    .param-header {
        color: #1E40AF;
        font-size: 24px;
        font-weight: bold;
        margin-bottom: 15px;
        border-bottom: 2px solid #E5E7EB;
        padding-bottom: 10px;
    }
    .stButton button {
        width: 100%;
    }
    </style>
    """, unsafe_allow_html=True)

    st.header("⚙️ Paramètres de l'application")

    # Onglets pour organiser les paramètres
    tab1, tab2, tab3 = st.tabs(["📂 Catégories", "💾 Maintenance & Export", "ℹ️ À propos"])

    # =======================
    # TAB 1: GESTION DES CATÉGORIES
    # =======================
    with tab1:
        st.markdown("<div class='param-header'>Gestion des Catégories</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.subheader("Nouvelle Catégorie")
            with st.form("add_category"):
                new_cat_name = st.text_input("Nom de la catégorie")
                new_cat_color = st.color_picker("Couleur", "#3B82F6")
                submitted = st.form_submit_button("Ajouter")
                
                if submitted:
                    if new_cat_name:
                        try:
                            # Vérifier si existe déjà
                            cats = database.get_all_categories()
                            if any(c['nom'].lower() == new_cat_name.lower() for c in cats):
                                st.error("Cette catégorie existe déjà.")
                            else:
                                database.add_categorie(new_cat_name, new_cat_color)
                                st.success(f"Catégorie '{new_cat_name}' ajoutée !")
                                st.rerun()
                        except Exception as e:
                            st.error(f"Erreur: {e}")
                    else:
                        st.warning("Veuillez entrer un nom.")

        with col2:
            st.subheader("Catégories existantes")
            categories = database.get_all_categories()
            if categories:
                # Affichage en tags colorés
                for cat in categories:
                    st.markdown(
                        f"""
                        <div style="
                            background-color: {cat['couleur']}20;
                            border: 1px solid {cat['couleur']};
                            padding: 10px;
                            border-radius: 8px;
                            margin-bottom: 8px;
                            display: flex;
                            align-items: center;
                            gap: 10px;
                        ">
                            <div style="width: 20px; height: 20px; background-color: {cat['couleur']}; border-radius: 50%;"></div>
                            <span style="font-weight: bold; font-size: 16px;">{cat['nom']}</span>
                        </div>
                        """, 
                        unsafe_allow_html=True
                    )
            else:
                st.info("Aucune catégorie définie.")

    # =======================
    # TAB 2: MAINTENANCE ET EXPORT
    # =======================
    with tab2:
        st.markdown("<div class='param-header'>Maintenance des Données</div>", unsafe_allow_html=True)
        
        col_backup, col_export = st.columns(2)
        
        # Section Backup
        with col_backup:
            st.subheader("Sauvegarde")
            st.markdown("Créez une copie de sécurité de la base de données actuelle.")
            
            if st.button("📦 Créer une sauvegarde (Backup)"):
                try:
                    backup_path = database.backup_database()
                    st.success(f"Sauvegarde réussie !")
                    st.code(backup_path)
                except Exception as e:
                    st.error(f"Erreur lors de la sauvegarde : {e}")

        # Section Export
        with col_export:
            st.subheader("Export CSV")
            st.markdown("Téléchargez les données au format CSV.")
            
            # Export Produits
            if st.button("📥 Exporter les Produits"):
                try:
                    csv_file = database.export_to_csv("produits")
                    with open(csv_file, "rb") as f:
                        st.download_button(
                            label="Télécharger CSV Produits",
                            data=f,
                            file_name=csv_file,
                            mime="text/csv"
                        )
                    # Nettoyage (optionnel, ou garder sur le serveur)
                    # os.remove(csv_file) 
                except Exception as e:
                    st.error(f"Erreur export produits: {e}")

            # Export Mouvements
            if st.button("📥 Exporter les Mouvements"):
                try:
                    csv_file = database.export_to_csv("mouvements")
                    with open(csv_file, "rb") as f:
                        st.download_button(
                            label="Télécharger CSV Mouvements",
                            data=f,
                            file_name=csv_file,
                            mime="text/csv"
                        )
                except Exception as e:
                    st.error(f"Erreur export mouvements: {e}")

    # =======================
    # TAB 3: À PROPOS
    # =======================
    with tab3:
        st.markdown("<div class='param-header'>À propos de StockFlow Pro</div>", unsafe_allow_html=True)
        
        st.info("""
        **StockFlow Pro** est une application de gestion de stock simple et efficace.
        
        - **Version**: 1.0.0
        - **Base de données**: SQLite
        - **Développé avec**: Python & Streamlit
        """)
        
        st.caption("© 2024 - Tous droits réservés")
