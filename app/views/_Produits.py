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
        background-color: #F8FAFC;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #E2E8F0;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 200px;
        transition: transform 0.2s;
    }
    .produit-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .produit-card h5 {
        margin: 0 0 5px 0;
        color: #1E40AF;
        font-weight: 600;
    }

    .produit-card p {
        margin: 4px 0;
        font-size: 14px;
        color: #475569;
    }
    
    .price-tag {
        font-weight: bold;
        color: #059669;
        font-size: 1.1em;
    }

    .produit-header {
        color: #1E40AF;
        font-size: 26px;
        font-weight: bold;
        margin-bottom: 20px;
        padding-bottom: 10px;
        border-bottom: 2px solid #E2E8F0;
    }
    </style>
    """, unsafe_allow_html=True)

    # =======================
    # Session State
    # =======================
    if 'refresh' not in st.session_state:
        st.session_state['refresh'] = False



    # =======================
    # Onglets
    # =======================
    tab1, tab2 = st.tabs(["📋 Liste des Produits", "➕ Ajouter un Produit"])

    # =======================
    # TAB 1: LISTE (CARDS)
    # =======================
    with tab1:
        search_term = st.text_input("🔍 Rechercher un produit par nom ou référence:", placeholder="Ex: Clavier, PROD-001...")

        try:
            produits = database.get_all_produits()
            if search_term:
                term = search_term.lower()
                produits = [
                    p for p in produits
                    if term in p['nom'].lower() or term in p['reference'].lower()
                ]
            
            st.markdown("<div class='produit-header'>Catalogue</div>", unsafe_allow_html=True)

            if produits:
                cols_per_row = 3
                for i in range(0, len(produits), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, p in enumerate(produits[i:i+cols_per_row]):
                        with cols[j]:
                            # Carte Produit
                            st.markdown(f"""
                            <div class='produit-card' style='border-left: 5px solid {p['categorie_couleur'] or '#ccc'};'>
                                <div>
                                    <h5>{p['nom']}<small style="color:#64748B;"> ({p['reference']})</small></h5>
                                    <p><b>Catégorie:</b> <span style='color: {p['categorie_couleur'] or '#333'}; font-weight: bold;'>{p['categorie_nom'] or '—'}</span></p>
                                    <p><b>Fournisseur:</b> {p['fournisseur_nom'] or '—'}</p>
                                    <p><b>Stock:</b> {p['quantite']} unités</p>
                                    <p class="price-tag">{p['prix_vente']} DH</p>
                                    <p style="font-style: italic; font-size: 12px; margin-top: 5px;">{p['description'] or ''}</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Bouton Supprimer
                            if st.button(f"🗑️ Supprimer", key=f"del_{p['id']}", help=f"Supprimer définitivement {p['nom']}"):
                                if database.delete_produit(p['id']):
                                    st.toast(f"Produit '{p['nom']}' supprimé avec succès !", icon="✅")
                                    st.rerun()
                                else:
                                    st.error("Erreur lors de la suppression.")
            else:
                if search_term:
                    st.info("Aucun produit ne correspond à votre recherche.")
                else:
                    st.info("Aucun produit dans la base de données. Commencez par en ajouter un !")

        except Exception as e:
            st.error(f"Erreur lors du chargement des produits: {e}")

    # =======================
    # TAB 2: AJOUT
    # =======================
    with tab2:
        st.subheader("Nouveau Produit")
        
        with st.form("ajout_produit", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                reference = st.text_input("Référence *")
                nom = st.text_input("Nom *")
                
                # Charger catégories
                cats = database.get_all_categories()
                if cats:
                    cats_dict = {c['id']: c['nom'] for c in cats}
                    categorie_id = st.selectbox("Catégorie *", options=list(cats_dict.keys()), format_func=lambda x: cats_dict[x])
                else:
                    st.warning("Aucune catégorie disponible. Veuillez en créer une dans Paramètres.")
                    categorie_id = None

            with col2:
                # Charger fournisseurs
                fours = database.get_all_fournisseurs()
                if fours:
                    fours_dict = {f['id']: f['nom'] for f in fours}
                    fournisseur_id = st.selectbox("Fournisseur", options=[None]+list(fours_dict.keys()), format_func=lambda x: fours_dict[x] if x else "Aucun")
                else:
                    fournisseur_id = None
                
                quantite = st.number_input("Quantité initiale", min_value=0, value=0)
                seuil_min = st.number_input("Seuil d'alerte", min_value=0, value=5)

            col3, col4 = st.columns(2)
            with col3:
                prix_achat = st.number_input("Prix d'achat (DH)", min_value=0.0, step=1.0)
            with col4:
                prix_vente = st.number_input("Prix de vente (DH)", min_value=0.0, step=1.0)
            
            description = st.text_area("Description", height=80)
            
            submitted = st.form_submit_button("💾 Enregistrer le produit", use_container_width=True)

            if submitted:
                if not reference or not nom or not categorie_id:
                    st.error("Veuillez remplir les champs obligatoires (*).")
                else:
                    try:
                        database.add_produit({
                            "reference": reference,
                            "nom": nom,
                            "description": description,
                            "categorie_id": categorie_id,
                            "fournisseur_id": fournisseur_id,
                            "quantite": quantite,
                            "seuil_min": seuil_min,
                            "prix_achat": prix_achat,
                            "prix_vente": prix_vente
                        })
                        st.toast(f"Produit '{nom}' ajouté avec succès !", icon="✅")
                    except ValueError as ve:
                        st.warning(str(ve))
                    except Exception as e:
                        st.error(f"Erreur technique : {e}")
