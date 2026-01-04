# views/_Users.py - Page de gestion des utilisateurs (Admin)
import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

def show():
    """Page de gestion des utilisateurs - Réservée aux administrateurs"""
    
    st.markdown("### 👥 Gestion des Utilisateurs")
    st.markdown("Gérez les comptes utilisateurs et leurs permissions")
    
    # Tabs
    tab1, tab2, tab3 = st.tabs(["📋 Liste des utilisateurs", "➕ Ajouter un utilisateur", "📊 Statistiques"])
    
    # TAB 1 : Liste des utilisateurs
    with tab1:
        st.markdown("#### Liste de tous les utilisateurs")
        
        conn = sqlite3.connect("stock.db")
        
        # Récupérer les utilisateurs
        query = """
            SELECT 
                id,
                username,
                email,
                full_name,
                role,
                created_at,
                last_login,
                is_active
            FROM users
            ORDER BY created_at DESC
        """
        
        df = pd.read_sql_query(query, conn)
        
        if df.empty:
            st.info("Aucun utilisateur trouvé")
        else:
            # Formatter les dates
            df['created_at'] = pd.to_datetime(df['created_at']).dt.strftime('%d/%m/%Y %H:%M')
            df['last_login'] = pd.to_datetime(df['last_login']).dt.strftime('%d/%m/%Y %H:%M')
            df['last_login'] = df['last_login'].fillna('Jamais connecté')
            
            # Renommer les colonnes
            df_display = df.copy()
            df_display.columns = ['ID', 'Utilisateur', 'Email', 'Nom complet', 'Rôle', 'Créé le', 'Dernière connexion', 'Actif']
            
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
            st.markdown("#### ⚙️ Actions sur les utilisateurs")
            
            col1, col2 = st.columns(2)
            
            with col1:
                user_ids = df['id'].tolist()
                usernames = df['username'].tolist()
                user_options = [f"{uid} - {uname}" for uid, uname in zip(user_ids, usernames)]
                
                selected_user = st.selectbox(
                    "Sélectionner un utilisateur",
                    user_options
                )
                
                if selected_user:
                    user_id = int(selected_user.split(' - ')[0])
                    user_info = df[df['id'] == user_id].iloc[0]
                    
                    st.info(f"""
                    **Informations:**
                    - Email: {user_info['email']}
                    - Rôle: {user_info['role']}
                    - Statut: {'✅ Actif' if user_info['is_active'] else '❌ Inactif'}
                    """)
            
            with col2:
                st.markdown("##### Actions disponibles")
                
                if st.button("🔄 Activer/Désactiver", use_container_width=True):
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users SET is_active = NOT is_active WHERE id = ?",
                        (user_id,)
                    )
                    conn.commit()
                    st.success("✅ Statut modifié")
                    st.rerun()
                
                if st.button("🔐 Réinitialiser mot de passe", use_container_width=True):
                    st.warning("⚠️ Le nouveau mot de passe sera : `reset123`")
                    from models.auth import AuthManager
                    auth = AuthManager()
                    new_hash = auth.hash_password("reset123")
                    
                    cursor = conn.cursor()
                    cursor.execute(
                        "UPDATE users SET password_hash = ? WHERE id = ?",
                        (new_hash, user_id)
                    )
                    conn.commit()
                    st.success("✅ Mot de passe réinitialisé")
                
                if st.button("🗑️ Supprimer l'utilisateur", use_container_width=True, type="primary"):
                    if user_info['username'] == 'admin':
                        st.error("❌ Impossible de supprimer le compte admin")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
                        conn.commit()
                        st.success("✅ Utilisateur supprimé")
                        st.rerun()
        
        conn.close()
    
    # TAB 2 : Ajouter un utilisateur
    with tab2:
        st.markdown("#### ➕ Créer un nouveau compte utilisateur")
        
        with st.form("add_user_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                new_username = st.text_input("👤 Nom d'utilisateur *")
                new_email = st.text_input("📧 Email *")
                new_fullname = st.text_input("👨‍💼 Nom complet")
            
            with col2:
                new_password = st.text_input("🔒 Mot de passe *", type="password")
                new_password_confirm = st.text_input("🔒 Confirmer *", type="password")
                new_role = st.selectbox("👑 Rôle", ["user", "admin"])
            
            submit = st.form_submit_button("✨ Créer le compte", use_container_width=True)
            
            if submit:
                if not all([new_username, new_email, new_password, new_password_confirm]):
                    st.error("❌ Veuillez remplir tous les champs obligatoires")
                elif new_password != new_password_confirm:
                    st.error("❌ Les mots de passe ne correspondent pas")
                else:
                    from models.auth import AuthManager
                    auth = AuthManager()
                    
                    # Créer l'utilisateur avec le rôle choisi
                    conn = sqlite3.connect("stock.db")
                    cursor = conn.cursor()
                    
                    try:
                        password_hash = auth.hash_password(new_password)
                        cursor.execute(
                            """INSERT INTO users (username, email, password_hash, full_name, role) 
                               VALUES (?, ?, ?, ?, ?)""",
                            (new_username, new_email, password_hash, new_fullname, new_role)
                        )
                        conn.commit()
                        st.success(f"✅ Compte '{new_username}' créé avec succès !")
                        st.balloons()
                    except sqlite3.IntegrityError as e:
                        if "username" in str(e):
                            st.error("❌ Ce nom d'utilisateur existe déjà")
                        else:
                            st.error("❌ Cet email est déjà utilisé")
                    
                    conn.close()
    
    # TAB 3 : Statistiques
    with tab3:
        st.markdown("#### 📊 Statistiques des utilisateurs")
        
        conn = sqlite3.connect("stock.db")
        cursor = conn.cursor()
        
        # Métriques
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            cursor.execute("SELECT COUNT(*) FROM users")
            total = cursor.fetchone()[0]
            st.metric("👥 Total utilisateurs", total)
        
        with col2:
            cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = 1")
            actifs = cursor.fetchone()[0]
            st.metric("✅ Actifs", actifs)
        
        with col3:
            cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
            admins = cursor.fetchone()[0]
            st.metric("👑 Administrateurs", admins)
        
        with col4:
            cursor.execute("SELECT COUNT(*) FROM users WHERE last_login IS NOT NULL")
            connectes = cursor.fetchone()[0]
            st.metric("🔐 Déjà connectés", connectes)
        
        st.markdown("---")
        
        # Graphique des connexions récentes
        st.markdown("##### 📈 Activité récente (7 derniers jours)")
        
        query_activity = """
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as tentatives,
                SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as succes
            FROM login_attempts
            WHERE timestamp >= date('now', '-7 days')
            GROUP BY DATE(timestamp)
            ORDER BY date
        """
        
        df_activity = pd.read_sql_query(query_activity, conn)
        
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
        
        query_last = """
            SELECT 
                la.username,
                la.timestamp
            FROM login_attempts la
            WHERE la.success = 1
            ORDER BY la.timestamp DESC
            LIMIT 10
        """
        
        df_last = pd.read_sql_query(query_last, conn)
        
        if not df_last.empty:
            df_last['timestamp'] = pd.to_datetime(df_last['timestamp']).dt.strftime('%d/%m/%Y %H:%M:%S')
            df_last.columns = ['Utilisateur', 'Date/Heure']
            st.dataframe(df_last, use_container_width=True, hide_index=True)
        else:
            st.info("Aucune connexion enregistrée")
        
        conn.close()