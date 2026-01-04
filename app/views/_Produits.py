
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
###
# app/pages/_Produits.py
import streamlit as st
from models import database

# =======================
# CSS personnalisé
# =======================
def show():
 st.markdown("""
<style>
.produit-card {
    background-color: #F0F0F0;
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 12px;
    box-shadow: 2px 2px 6px #d1d5db;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 200px;
}

.produit-card h5 {
    margin: 0 0 5px 0;
    color: #1E40AF;
}

.produit-card p {
    margin: 2px 0;
    font-size: 14px;
}

.produit-header {
    color: #1E40AF;
    font-size: 26px;
    font-weight: bold;
    margin-bottom: 10px;
}
</style>
""", unsafe_allow_html=True)

# =======================
# Session State
# =======================
 if 'refresh' not in st.session_state:
    st.session_state['refresh'] = False

# =======================
# Fonction pour afficher la liste
# =======================
 def afficher_produits():
    search_term = st.text_input("🔍 Rechercher un produit par nom ou référence:")

    try:
        produits = database.get_all_produits()
        if search_term:
            term = search_term.lower()
            produits = [
                p for p in produits
                if term in p['nom'].lower() or term in p['reference'].lower()
            ]
        
        st.markdown("<div class='produit-header'>Liste des produits existants</div>", unsafe_allow_html=True)

        if produits:
            cols_per_row = 3
            for i in range(0, len(produits), cols_per_row):
                cols = st.columns(cols_per_row)
                for j, p in enumerate(produits[i:i+cols_per_row]):
                    with cols[j]:
                        st.markdown(f"""
                        <div class='produit-card'>
                            <div>
                                <h5>{p['nom']}<small> ({p['reference']})</small></h5>
                                <p><b>Catégorie:</b> {p['categorie_nom'] or '—'}</p>
                                <p><b>Fournisseur:</b> {p['fournisseur_nom'] or '—'}</p>
                                <p><b>Quantité:</b> {p['quantite']} | <b>Prix Vente:</b> {p['prix_vente']} €</p>
                                <p>{p['description']}</p>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

                        # Bouton Supprimer
                        if st.button(f"Supprimer {p['nom']}", key=f"del_{p['id']}"):
                            if database.delete_produit(p['id']):
                                st.success(f"Produit '{p['nom']}' supprimé !")
                                # Toggle refresh pour réafficher
                                st.session_state['refresh'] = not st.session_state['refresh']
                            else:
                                st.error("Erreur lors de la suppression")
        else:
            st.info("Aucun produit correspondant à la recherche.")
    except Exception as e:
        st.error(f"Erreur lors du chargement des produits: {e}")

# =======================
# Formulaire Ajouter Produit
# =======================
 with st.expander("➕ Ajouter un produit"):
    with st.form("ajout_produit"):
        col1, col2 = st.columns(2)
        with col1:
            reference = st.text_input("Référence")
            nom = st.text_input("Nom")
            categorie = st.selectbox(
                "Catégorie",
                [c['nom'] for c in database.get_all_categories()]
            )
        with col2:
            fournisseur = st.selectbox(
                "Fournisseur",
                [f['nom'] for f in database.get_all_fournisseurs()]
            )
            quantite = st.number_input("Quantité", min_value=0, value=0)
            prix_vente = st.number_input("Prix de vente (€)", min_value=0.0, value=0.0, step=0.5)
        
        description = st.text_area("Description", height=50)
        submitted = st.form_submit_button("Ajouter")

        if submitted:
            cat_obj = next((c for c in database.get_all_categories() if c['nom'] == categorie), None)
            four_obj = next((f for f in database.get_all_fournisseurs() if f['nom'] == fournisseur), None)
            try:
                database.add_produit({
                    "reference": reference,
                    "nom": nom,
                    "description": description,
                    "categorie_id": cat_obj['id'] if cat_obj else None,
                    "fournisseur_id": four_obj['id'] if four_obj else None,
                    "quantite": quantite,
                    "prix_vente": prix_vente
                })
                st.success(f"Produit '{nom}' ajouté avec succès !")
                st.session_state['refresh'] = not st.session_state['refresh']
            except Exception as e:
                st.error(f"Erreur lors de l'ajout : {e}")

 st.markdown("---")

# =======================
# Afficher les produits
# =======================
# Appeler la fonction d'affichage et réafficher automatiquement si refresh change
 afficher_produits()

