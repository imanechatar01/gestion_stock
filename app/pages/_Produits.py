# app/pages/_Produits.py - Page Gestion des Produits
import streamlit as st
import pandas as pd
from models import database

def show():
    st.title("📦 Gestion des Produits")
    
    tab1, tab2 = st.tabs(["📋 Liste des Produits", "➕ Ajouter un Produit"])
    
    with tab1:
        st.subheader("Liste complète des produits")
        
        # Récupérer les produits
        produits = database.get_all_produits()
        
        if produits:
            df = pd.DataFrame(produits)
            
            # Afficher le tableau
            st.dataframe(
                df[['reference', 'nom', 'categorie_nom', 'quantite', 'prix_vente']],
                column_config={
                    "reference": "Référence",
                    "nom": "Nom",
                    "categorie_nom": "Catégorie",
                    "quantite": "Stock",
                    "prix_vente": "Prix (€)"
                },
                use_container_width=True
            )
            
            # Bouton d'export
            if st.button("📥 Exporter en CSV"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Télécharger CSV",
                    data=csv,
                    file_name="produits.csv",
                    mime="text/csv"
                )
        else:
            st.info("Aucun produit enregistré")
    
    with tab2:
        st.subheader("Ajouter un nouveau produit")
        
        with st.form("form_ajout_produit", clear_on_submit=True):
            col1, col2 = st.columns(2)
            
            with col1:
                reference = st.text_input("Référence *")
                nom = st.text_input("Nom du produit *")
                
                # Catégories depuis la base
                categories = database.get_all_categories()
                if categories:
                    categories_dict = {cat['id']: cat['nom'] for cat in categories}
                    categorie_id = st.selectbox(
                        "Catégorie *",
                        options=list(categories_dict.keys()),
                        format_func=lambda x: categories_dict[x]
                    )
                else:
                    st.warning("Créez d'abord des catégories")
                    categorie_id = 1
            
            with col2:
                quantite = st.number_input("Quantité initiale", min_value=0, value=0)
                seuil_min = st.number_input("Seuil d'alerte", min_value=1, value=5)
                prix_achat = st.number_input("Prix d'achat (€)", min_value=0.0, value=0.0)
                prix_vente = st.number_input("Prix de vente (€)", min_value=0.0, value=0.0)
            
            description = st.text_area("Description", height=100)
            
            # Fournisseurs depuis la base
            fournisseurs = database.get_all_fournisseurs()
            if fournisseurs:
                fournisseurs_dict = {four['id']: four['nom'] for four in fournisseurs}
                fournisseur_id = st.selectbox(
                    "Fournisseur",
                    options=[None] + list(fournisseurs_dict.keys()),
                    format_func=lambda x: "Sélectionnez..." if x is None else fournisseurs_dict[x]
                )
            else:
                fournisseur_id = None
            
            submitted = st.form_submit_button("💾 Enregistrer le produit")
            
            if submitted:
                if reference and nom:
                    try:
                        produit_id = database.add_produit(
                            reference, nom, description, categorie_id, 
                            fournisseur_id, quantite, seuil_min, 
                            prix_achat, prix_vente
                        )
                        st.success(f"✅ Produit '{nom}' ajouté avec succès (ID: {produit_id})")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Erreur: {str(e)}")
                else:
                    st.error("❌ Les champs marqués * sont obligatoires")