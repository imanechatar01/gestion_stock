# views/_Users.py - Page de gestion des utilisateurs (Admin)
import streamlit as st
import pandas as pd
from datetime import datetime
from models import database

def show():
    """Page de gestion des employés - Réservée aux administrateurs"""
    
    st.markdown("### 👥 Gestion des Employés")
    st.markdown("Gérez les comptes employés et leurs permissions d'accès")
    
    col_actions, col_empty = st.columns([1, 4])
    with col_actions:
        if st.button("➕ Enregistrer un Employé", type="primary", use_container_width=True):
            st.session_state.mode = 'create_user'
            st.rerun()

    # Tabs
    tab1, tab2 = st.tabs(["📋 Liste des employés", "📊 Statistiques"])
    
    # TAB 1 : Liste des utilisateurs
    with tab1:
        st.markdown("#### Liste de tous les employés")
        
        # Récupérer les utilisateurs via la couche database
        users = database.get_all_users()
        df = pd.DataFrame(users)
        
        if df.empty:
            st.info("Aucun utilisateur trouvé")
        else:
            # Formatter les dates
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%d/%m/%Y %H:%M')
            df['last_login'] = pd.to_datetime(df['last_login']).dt.strftime('%d/%m/%Y %H:%M')
            df['last_login'] = df['last_login'].fillna('Jamais connecté')
            
            # Renommer les colonnes
            df_display = df.copy()
            df_display.columns = ['ID', 'Employé', 'Email', 'Nom complet', 'Rôle', 'Permissions', 'Créé le', 'Dernière connexion', 'Actif']
            
            # Afficher avec style
            st.dataframe(
                df_display,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Actif": st.column_config.CheckboxColumn("Actif"),
                    "Rôle": st.column_config.TextColumn("Rôle"),
                }
            )
            
            st.markdown("---")
            
            # Actions sur les utilisateurs
            st.markdown("#### ⚙️ Actions sur les employés")
            
            col1, col2 = st.columns(2)
            
            with col1:
                user_ids = df['id'].tolist()
                usernames = df['username'].tolist()
                user_options = [f"{uid} - {uname}" for uid, uname in zip(user_ids, usernames)]
                
                selected_user = st.selectbox(
                    "Sélectionner un employé",
                    user_options
                )
                
                if selected_user:
                    user_id = int(selected_user.split(' - ')[0])
                    user_info = df[df['id'] == user_id].iloc[0]
                    
                    st.info(f"""
                    **Informations:**
                    - Email: {user_info['email']}
                    - Rôle: {user_info['role']}
                    - Permissions: {user_info['permissions'] or 'Aucune'}
                    - Statut: {'✅ Actif' if user_info['is_active'] else '❌ Inactif'}
                    """)
            
            with col2:
                st.markdown("##### Actions disponibles")
                
                if st.button("🔄 Activer/Désactiver", use_container_width=True):
                    database.update_user_field(user_id, 'is_active', not user_info['is_active'])
                    st.success("✅ Statut modifié")
                    st.rerun()
                
                if st.button("🔐 Réinitialiser mot de passe", use_container_width=True):
                    st.warning("⚠️ Le nouveau mot de passe sera : `reset123`")
                    from models.auth import AuthManager
                    auth = AuthManager()
                    new_hash = auth.hash_password("reset123")
                    
                    database.update_user_field(user_id, 'password_hash', new_hash)
                    st.success("✅ Mot de passe réinitialisé")
                
                if st.button("🗑️ Supprimer l'employé", use_container_width=True, type="primary"):
                    if user_info['username'] == 'admin':
                        st.error("❌ Impossible de supprimer le compte admin")
                    else:
                        database.delete_user(user_id)
                        st.success("✅ Employé supprimé")
                        st.rerun()
        
        conn.close()
    
    # TAB 2 : Statistiques (Redirigé depuis tab3 original)
    with tab2:
        st.markdown("#### 📊 Statistiques des utilisateurs")
        
        # Métriques
        stats = database.get_user_metrics()
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("👥 Total utilisateurs", stats['total'])
        
        with col2:
            st.metric("✅ Actifs", stats['actifs'])
        
        with col3:
            st.metric("👑 Administrateurs", stats['admins'])
        
        with col4:
            st.metric("🔐 Déjà connectés", stats['connectes'])
        
        st.markdown("---")
        
        # Graphique des connexions récentes
        st.markdown("##### 📈 Activité récente (7 derniers jours)")
        
        activity_data = database.get_login_activity_data()
        df_activity = pd.DataFrame(activity_data)
        
        if not df_activity.empty:
            df_activity['date'] = pd.to_datetime(df_activity['date'])
            
            st.line_chart(
                df_activity.set_index('date')[['tentatives', 'succes']],
                use_container_width=True
            )
        else:
            st.info("Aucune activité récente")
        
        # Dernières connexions
        st.markdown("##### 🕐 Dernières connexions réussies")
        
        last_logins = database.get_recent_successful_logins()
        df_last = pd.DataFrame(last_logins)
        
        if not df_last.empty:
            df_last['timestamp'] = pd.to_datetime(df_last['timestamp']).dt.strftime('%d/%m/%Y %H:%M:%S')
            df_last.columns = ['Utilisateur', 'Date/Heure']
            st.dataframe(df_last, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune connexion enregistrée")