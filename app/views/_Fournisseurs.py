# app/pages/_Fournisseurs.py
import streamlit as st
from models import database

# =======================
# CSS personnalisé
# =======================
def show():
    st.markdown("""
    <style>
    .fournisseur-card {
        background-color: #F0F0F0;
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 12px;
        box-shadow: 2px 2px 6px #d1d5db;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 150px;
    }

    .fournisseur-card h5 {
        margin: 0 0 5px 0;
        color: #1E40AF;
    }

    .fournisseur-card p {
        margin: 2px 0;
        font-size: 14px;
    }

    .fournisseur-header {
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
    if 'refresh_fournisseurs' not in st.session_state:
        st.session_state['refresh_fournisseurs'] = False

# =======================
# Fonction pour afficher la liste
# =======================
    def afficher_fournisseurs():
        search_term = st.text_input("🔍 Rechercher un fournisseur par nom ou email:")

        try:
            fournisseurs = database.get_all_fournisseurs()
            if search_term:
                term = search_term.lower()
                fournisseurs = [
                    f for f in fournisseurs
                    if term in f['nom'].lower() or (f['email'] and term in f['email'].lower())
                ]
            
            st.markdown("<div class='fournisseur-header'>Liste des fournisseurs</div>", unsafe_allow_html=True)

            if fournisseurs:
                cols_per_row = 3
                for i in range(0, len(fournisseurs), cols_per_row):
                    cols = st.columns(cols_per_row)
                    for j, f in enumerate(fournisseurs[i:i+cols_per_row]):
                        with cols[j]:
                            st.markdown(f"""
                            <div class='fournisseur-card'>
                                <div>
                                    <h5>{f['nom']}</h5>
                                    <p><b>Email:</b> {f['email'] or '—'}</p>
                                    <p><b>Téléphone:</b> {f['telephone'] or '—'}</p>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)

                            # Bouton Supprimer
                            if st.button(f"Supprimer {f['nom']}", key=f"del_fourn_{f['id']}"):
                                try:
                                    if database.delete_fournisseur(f['id']):
                                        st.success(f"Fournisseur '{f['nom']}' supprimé !")
                                        st.session_state['refresh_fournisseurs'] = not st.session_state['refresh_fournisseurs']
                                    else:
                                        st.error("Erreur lors de la suppression.")
                                except Exception as e:
                                    st.error(f"Erreur: {e}")
            else:
                st.info("Aucun fournisseur trouvé.")
        except Exception as e:
            st.error(f"Erreur lors du chargement des fournisseurs: {e}")

# =======================
# Formulaire Ajouter Fournisseur
# =======================
    with st.expander("➕ Ajouter un fournisseur"):
        with st.form("ajout_fournisseur"):
            col1, col2 = st.columns(2)
            with col1:
                nom = st.text_input("Nom du fournisseur (obligatoire)")
                email = st.text_input("Email")
            with col2:
                telephone = st.text_input("Téléphone")
            
            submitted = st.form_submit_button("Ajouter")

            if submitted:
                if not nom:
                    st.error("Le nom est obligatoire.")
                else:
                    try:
                        database.add_fournisseur(nom, email, telephone)
                        st.success(f"Fournisseur '{nom}' ajouté avec succès !")
                        st.session_state['refresh_fournisseurs'] = not st.session_state['refresh_fournisseurs']
                    except Exception as e:
                        st.error(f"Erreur lors de l'ajout : {e}")

    st.markdown("---")

# =======================
# Afficher les fournisseurs
# =======================
    afficher_fournisseurs()
