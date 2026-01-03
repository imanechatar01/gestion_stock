# app/pages/_Produits.py
import streamlit as st
from models import database

# =======================
# CSS personnalisé
# =======================
st.markdown("""
<style>
.produit-card {
    background-color: #F0F0F0;  /* gris clair */
    padding: 15px;
    border-radius: 12px;
    margin-bottom: 12px;
    box-shadow: 2px 2px 6px #d1d5db;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    min-height: 220px;  /* même hauteur */
}

.produit-card h5 {
    margin: 0 0 5px 0;  /* réduit espace après le titre */
    color: #1E40AF;
}

.produit-card p {
    margin: 2px 0;  /* réduit espace entre paragraphes */
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
# Session State pour rafraîchissement
# =======================
if 'refresh' not in st.session_state:
    st.session_state['refresh'] = False

# =======================
# Fonction principale
# =======================
def show():
    st.subheader("")

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
                # Récupérer les IDs
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
                    # Mettre à jour le refresh
                    st.session_state['refresh'] = not st.session_state['refresh']
                except Exception as e:
                    st.error(f"Erreur lors de l'ajout : {e}")

    st.markdown("---")

    # =======================
    # Barre de recherche
    # =======================
    search_term = st.text_input("🔍 Rechercher un produit par nom ou référence:")

    # =======================
    # Liste des produits
    # =======================
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
                                st.session_state['refresh'] = not st.session_state['refresh']
                            else:
                                st.error("Erreur lors de la suppression")
        else:
            st.info("Aucun produit correspondant à la recherche.")
    except Exception as e:
        st.error(f"Erreur lors du chargement des produits: {e}")
