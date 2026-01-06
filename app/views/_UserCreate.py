import streamlit as st
from models.auth import AuthManager

def show():
    # Style personnalisé
    st.markdown("""
        <style>
        .stForm {
            background-color: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        </style>
    """, unsafe_allow_html=True)

    col_header_1, col_header_2 = st.columns([1, 5])
    with col_header_1:
        if st.button("⬅️ Retour", key="back_btn"):
            if 'mode' in st.session_state:
                del st.session_state.mode
            st.rerun()
    
    with col_header_2:
        st.markdown("## 👤 Enregistrement d'un Nouvel Employé")

    # Conteneur centré pour le formulaire
    with st.container():
        with st.form("create_user_full_form"):
            st.markdown("### Informations Générales")
            
            col1, col2 = st.columns(2)
            
            with col1:
                username = st.text_input("Identifiant (login) *")
                full_name = st.text_input("Nom complet")
                email = st.text_input("Email *")
            
            with col2:
                password = st.text_input("Mot de passe *", type="password")
                password_conf = st.text_input("Confirmer mot de passe *", type="password")
                role = st.selectbox("Rôle", ["user", "admin"], help="Admin a accès à tout par défaut")

            st.markdown("---")
            st.markdown("### 🔒 Permissions d'Accès")
            st.info("Sélectionnez les parties de l'application accessibles pour cet employé.")

            # Liste des permissions disponibles
            perms_map = {
                "dashboard": "🏠 Tableau de Bord",
                "produits": "📦 Gestion Produits",
                "inventaire": "📊 Inventaire & Stock",
                "fournisseurs": "👥 Fournisseurs",
                "rapports": "📈 Rapports (Lecture seule)",
                "alertes": "⚠️ Alertes de Stock"
            }
            
            # Admins have all permissions implicitly, but we save them anyway
            # Users need specific selection
            
            selected_perms = st.multiselect(
                "Modules autorisés",
                options=list(perms_map.keys()),
                format_func=lambda x: perms_map[x],
                default=["dashboard", "produits", "inventaire"],
                help="L'employé ne verra que les modules sélectionnés dans son menu."
            )

            st.markdown("---")
            
            submitted = st.form_submit_button("✨ Enregistrer l'Employé", type="primary", use_container_width=True)
            
            if submitted:
                # Validation basique
                if not all([username, email, password, password_conf]):
                    st.error("❌ Veuillez remplir tous les champs obligatoires (*)")
                    return

                if password != password_conf:
                    st.error("❌ Les mots de passe ne correspondent pas")
                    return

                # Auth Manager
                auth = AuthManager()
                
                # Convert permissions to string
                perms_str = ",".join(selected_perms)
                
                # Si admin, on ajoute tout (optionnel, mais bon pour la sécurité)
                if role == 'admin':
                    perms_str += ",parametres,utilisateurs"

                # Création
                success, msg = auth.register(
                    username=username,
                    email=email,
                    password=password,
                    full_name=full_name,
                    permissions=perms_str
                )
                
                if success:
                    st.success(f"✅ {msg}")
                    st.balloons()
                    # On ne retourne pas automatiquement pour laisser le temps de voir le message
                else:
                    st.error(f"❌ {msg}")
