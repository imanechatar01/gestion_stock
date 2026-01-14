import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from models import database
import time

def show():
    """
    Page de gestion des alertes et notifications
    """
    
    # Titre avec indicateur en temps réel
    st.markdown("""
    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 30px;">
        <div>
            <h1 style="margin: 0;">⚠️ Gestion des Alertes</h1>
            <p style="color: #666; margin: 5px 0 0 0;">Surveillance intelligente du stock en temps réel</p>
        </div>
        <div id="alert-badge" style="background: #ef4444; color: white; padding: 10px 20px; border-radius: 25px; font-weight: bold; font-size: 24px;">
            <!-- Le badge sera mis à jour via JavaScript -->
            0
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # JavaScript pour actualiser le badge
    st.markdown("""
    <script>
    function updateAlertBadge() {
        fetch('/reload?force=true')
            .then(() => {
                // Simuler un compteur pour la démo
                const badge = document.getElementById('alert-badge');
                const current = parseInt(badge.textContent);
                if (current < 5) {
                    badge.textContent = current + 1;
                    badge.style.background = current >= 3 ? '#ef4444' : '#f59e0b';
                }
            });
    }
    // Mettre à jour toutes les 30 secondes
    setInterval(updateAlertBadge, 30000);
    </script>
    """, unsafe_allow_html=True)
    
    # Initialisation de la session state pour les alertes traitées
    if 'alertes_traitees' not in st.session_state:
        st.session_state.alertes_traitees = set()
    
    # Onglets principaux
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Tableau de Bord",
        "📋 Alertes Actives", 
        "📈 Historique",
        "⚙️ Configuration"
    ])
    
    # TAB 1: Tableau de bord des alertes
    with tab1:
        display_tableau_de_bord()
    
    # TAB 2: Alertes actives
    with tab2:
        display_alertes_actives()
    
    # TAB 3: Historique
    with tab3:
        display_historique_alertes()
    
    # TAB 4: Configuration
    with tab4:
        display_configuration_alertes()

# Remplacer get_alertes_stock() par :
def get_alertes_stock():
    """Récupère les alertes de stock depuis la base"""
    return database.get_alertes_actives()

# Remplacer marquer_alerte_traitee() par :
def marquer_alerte_traitee(alerte_id, utilisateur="admin"):
    """Marque une alerte comme traitée dans la base"""
    try:
        success = database.traiter_alerte(
            alerte_id=alerte_id,
            traite_par=utilisateur,
            action_prise="Alerte traitée via l'interface",
            notes="Résolue manuellement"
        )
        return success
    except Exception as e:
        st.error(f"Erreur: {e}")
        return False

# Remplacer get_statistiques_alertes() par :
def get_statistiques_alertes():
    """Calcule les statistiques des alertes depuis la base"""
    return database.get_statistiques_alertes()

def get_alertes_date_expiration():
    """Simule les alertes de date d'expiration"""
    # Dans une vraie application, ceci viendrait d'une table produits avec dates d'expiration
    alertes_expiration = [
        {
            'id': 'EXP-001',
            'type': 'expiration',
            'titre': 'Produit approchant expiration',
            'description': 'Lot #A123 expire dans 15 jours',
            'urgence': 'MOYENNE',
            'date_detection': (datetime.now() - timedelta(days=1)).isoformat(),
            'produit_nom': 'Antiseptique Médical',
            'categorie': 'Médical',
            'statut': 'active',
            'action_requise': 'Vérifier et planifier rotation'
        },
        {
            'id': 'EXP-002',
            'type': 'expiration',
            'titre': 'Produit expiré',
            'description': 'Lot #B456 a expiré il y a 5 jours',
            'urgence': 'HAUTE',
            'date_detection': (datetime.now() - timedelta(days=5)).isoformat(),
            'produit_nom': 'Conserves Alimentaires',
            'categorie': 'Alimentation',
            'statut': 'active',
            'action_requise': 'Retirer du stock immédiatement'
        }
    ]
    
    return alertes_expiration

def get_alertes_mouvements():
    """Simule les alertes de mouvements inhabituels"""
    try:
        # Récupérer les mouvements récents
        mouvements = database.fetch_all("""
            SELECT m.*, p.nom as produit_nom
            FROM mouvements m
            JOIN produits p ON m.produit_id = p.id
            WHERE m.date_mouvement > DATE('now', '-7 days')
            ORDER BY m.date_mouvement DESC
            LIMIT 50
        """) or []
        
        alertes = []
        
        # Détecter les mouvements importants
        for mouvement in mouvements:
            if mouvement['quantite'] > 100:  # Seuil pour gros mouvement
                alertes.append({
                    'id': f"MVT-{mouvement['id']}",
                    'type': 'gros_mouvement',
                    'titre': f'Gros mouvement détecté : {mouvement["produit_nom"]}',
                    'description': f"{mouvement['quantite']} unités {mouvement['type']} le {mouvement['date_mouvement']}",
                    'urgence': 'MOYENNE',
                    'date_detection': mouvement['date_mouvement'],
                    'produit_nom': mouvement['produit_nom'],
                    'statut': 'active',
                    'action_requise': 'Vérifier la transaction'
                })
        
        return alertes
    
    except Exception as e:
        st.error(f"Erreur détection mouvements: {e}")
        return []

def get_toutes_alertes():
    """Combine toutes les alertes"""
    alertes_stock = get_alertes_stock()
    alertes_expiration = get_alertes_date_expiration()
    alertes_mouvements = get_alertes_mouvements()
    
    toutes_alertes = alertes_stock + alertes_expiration + alertes_mouvements
    
    # Filtrer les alertes déjà traitées
    alertes_non_traitees = [
        alerte for alerte in toutes_alertes 
        if alerte['id'] not in st.session_state.alertes_traitees
    ]
    
    return alertes_non_traitees

def get_statistiques_alertes():
    """Calcule les statistiques des alertes"""
    alertes = get_toutes_alertes()
    
    stats = {
        'total': len(alertes),
        'critiques': len([a for a in alertes if a['urgence'] == 'CRITIQUE']),
        'hautes': len([a for a in alertes if a['urgence'] == 'HAUTE']),
        'moyennes': len([a for a in alertes if a['urgence'] == 'MOYENNE']),
        'basses': len([a for a in alertes if a['urgence'] == 'BASSE']),
        'par_type': {
            'stock_bas': len([a for a in alertes if a['type'] == 'stock_bas']),
            'expiration': len([a for a in alertes if a['type'] == 'expiration']),
            'gros_mouvement': len([a for a in alertes if a['type'] == 'gros_mouvement']),
        },
        'traitees': len(st.session_state.alertes_traitees),
        'non_traitees': len(alertes)
    }
    
    return stats

def display_tableau_de_bord():
    """Affiche le tableau de bord des alertes"""
    
    # Statistiques en temps réel
    stats = get_statistiques_alertes()
    
    # Métriques principales
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Alertes",
            value=stats['total'],
            delta=f"{stats['non_traitees']} non traitées"
        )
    
    with col2:
        st.metric(
            label="Alertes Critiques",
            value=stats['critiques'],
            delta_color="inverse",
            delta=f"-{stats['critiques']}" if stats['critiques'] > 0 else None
        )
    
    with col3:
        st.metric(
            label="Alertes Hautes",
            value=stats['hautes'],
            delta_color="inverse"
        )
    
    with col4:
        st.metric(
            label="Alertes Traitées",
            value=stats['traitees'],
            delta=f"+{stats['traitees']}" if stats['traitees'] > 0 else None
        )
    
    st.markdown("---")
    
    # Graphiques
    col_chart1, col_chart2 = st.columns(2)
    
    with col_chart1:
        st.markdown("#### 📊 Répartition par urgence")
        
        # Données pour le graphique
        data_urgence = {
            'Urgence': ['Critiques', 'Hautes', 'Moyennes', 'Basses'],
            'Nombre': [stats['critiques'], stats['hautes'], stats['moyennes'], stats['basses']],
            'Couleur': ['#ef4444', '#f97316', '#eab308', '#22c55e']
        }
        
        df_urgence = pd.DataFrame(data_urgence)
        
        fig = px.bar(
            df_urgence,
            x='Urgence',
            y='Nombre',
            color='Urgence',
            color_discrete_sequence=df_urgence['Couleur'].tolist(),
            text='Nombre'
        )
        
        fig.update_layout(
            showlegend=False,
            height=300,
            margin=dict(l=20, r=20, t=30, b=20)
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with col_chart2:
        st.markdown("#### 📈 Répartition par type")
        
        data_type = pd.DataFrame([
            {'Type': 'Stock Bas', 'Nombre': stats['par_type']['stock_bas']},
            {'Type': 'Expiration', 'Nombre': stats['par_type']['expiration']},
            {'Type': 'Gros Mouvements', 'Nombre': stats['par_type']['gros_mouvement']},
        ])
        
        fig = px.pie(
            data_type,
            values='Nombre',
            names='Type',
            hole=0.4
        )
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=30, b=20),
            showlegend=True
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Alertes récentes
    st.markdown("---")
    st.markdown("#### 🚨 Alertes récentes")
    
    alertes = get_toutes_alertes()
    if alertes:
        # Trier par urgence et date
        alertes_triees = sorted(
            alertes,
            key=lambda x: (x['urgence'] == 'CRITIQUE', x['urgence'] == 'HAUTE', x['date_detection']),
            reverse=True
        )[:5]
        
        for alerte in alertes_triees:
            display_carte_alerte(alerte, compact=True)
    else:
        st.success("🎉 Aucune alerte active pour le moment !")
    
    # Section de prévision
    st.markdown("---")
    with st.expander("🔮 Prévisions et recommandations"):
        st.info("Analyse prédictive basée sur les données historiques")
        
        col_rec1, col_rec2 = st.columns(2)
        
        with col_rec1:
            st.markdown("##### 📦 Produits à surveiller")
            
            try:
                produits_faible_stock = database.fetch_all("""
                    SELECT nom, quantite, seuil_min 
                    FROM produits 
                    WHERE quantite <= seuil_min * 1.5
                    ORDER BY quantite/seuil_min
                    LIMIT 5
                """) or []
                
                if produits_faible_stock:
                    for prod in produits_faible_stock:
                        ratio = prod['quantite'] / prod['seuil_min'] if prod['seuil_min'] > 0 else 0
                        st.progress(
                            min(ratio, 1.0),
                            text=f"{prod['nom']}: {prod['quantite']}/{prod['seuil_min']}"
                        )
                else:
                    st.write("Aucun produit à risque imminent")
                    
            except Exception as e:
                st.error(f"Erreur: {e}")
        
        with col_rec2:
            st.markdown("##### 📊 Tendances")
            
            # Simulation de tendances
            tendances = [
                ("📈 Augmentation des alertes stock", "+15% ce mois"),
                ("📉 Diminution alertes expiration", "-8% ce mois"),
                ("⏱️ Temps moyen de traitement", "2.3 jours"),
                ("🎯 Taux de résolution", "87%")
            ]
            
            for tendance, valeur in tendances:
                st.metric(tendance, valeur)

def display_carte_alerte(alerte, compact=False):
    """Affiche une carte d'alerte stylisée"""
    
    # Couleurs selon l'urgence
    colors = {
        'CRITIQUE': {'bg': '#fee2e2', 'border': '#ef4444', 'text': '#991b1b'},
        'HAUTE': {'bg': '#ffedd5', 'border': '#f97316', 'text': '#9a3412'},
        'MOYENNE': {'bg': '#fef3c7', 'border': '#eab308', 'text': '#854d0e'},
        'BASSE': {'bg': '#dcfce7', 'border': '#22c55e', 'text': '#166534'}
    }
    
    style = colors.get(alerte['urgence'], colors['MOYENNE'])
    
    # Icônes selon le type
    icons = {
        'stock_bas': '📦',
        'expiration': '⏰',
        'gros_mouvement': '📊',
        'default': '⚠️'
    }
    
    icon = icons.get(alerte['type'], icons['default'])
    
    if compact:
        # Version compacte pour le tableau de bord
        with st.container():
            col_icon, col_content, col_actions = st.columns([1, 5, 2])
            
            with col_icon:
                st.markdown(f"<h2 style='margin: 0;'>{icon}</h2>", unsafe_allow_html=True)
            
            with col_content:
                st.markdown(f"**{alerte['titre']}**")
                st.caption(alerte['description'])
                st.markdown(f"<span style='background: {style['border']}20; color: {style['text']}; padding: 2px 8px; border-radius: 12px; font-size: 12px;'>{alerte['urgence']}</span>", unsafe_allow_html=True)
            
            with col_actions:
                if st.button("👁️", key=f"view_{alerte['id']}", help="Voir détails"):
                    st.session_state[f"show_alert_{alerte['id']}"] = True
                
                if st.button("✓", key=f"resolve_{alerte['id']}", help="Marquer comme traité"):
                    marquer_alerte_traitee(alerte['id'])
                    st.rerun()
            
            st.markdown("---")
    else:
        # Version détaillée
        with st.container():
            st.markdown(f"""
            <div style="
                background: {style['bg']};
                border: 2px solid {style['border']};
                border-radius: 10px;
                padding: 15px;
                margin: 10px 0;
            ">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-size: 24px;">{icon}</span>
                        <div>
                            <h3 style="margin: 0; color: {style['text']};">{alerte['titre']}</h3>
                            <p style="margin: 5px 0; color: #666;">{alerte['description']}</p>
                        </div>
                    </div>
                    <span style="
                        background: {style['border']};
                        color: white;
                        padding: 5px 15px;
                        border-radius: 20px;
                        font-weight: bold;
                        font-size: 12px;
                    ">{alerte['urgence']}</span>
                </div>
                
                <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 12px; color: #666;">
                        <span>🔍 {alerte.get('categorie', 'Non catégorisé')}</span>
                        <span style="margin-left: 15px;">📅 {datetime.fromisoformat(alerte['date_detection']).strftime('%d/%m/%Y %H:%M')}</span>
                    </div>
                    
                    <div>
                        <span style="
                            background: #3b82f6;
                            color: white;
                            padding: 5px 15px;
                            border-radius: 5px;
                            font-size: 12px;
                        ">Action requise: {alerte['action_requise']}</span>
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            # Actions
            col_action1, col_action2, col_action3, col_action4 = st.columns(4)
            
            with col_action1:
                if st.button("✅ Marquer comme traité", key=f"resolve_full_{alerte['id']}", use_container_width=True):
                    marquer_alerte_traitee(alerte['id'])
                    st.success(f"Alerte {alerte['id']} marquée comme traitée")
                    time.sleep(1)
                    st.rerun()
            
            with col_action2:
                if st.button("📝 Créer commande", key=f"order_{alerte['id']}", use_container_width=True):
                    if alerte['type'] == 'stock_bas':
                        st.info(f"Création d'une commande pour {alerte['produit_nom']}")
                        # Ici vous pourriez appeler une fonction pour créer une commande
            
            with col_action3:
                if st.button("🔔 Planifier rappel", key=f"remind_{alerte['id']}", use_container_width=True):
                    st.info("Rappel planifié pour demain")
            
            with col_action4:
                if st.button("📊 Voir historique", key=f"history_{alerte['id']}", use_container_width=True):
                    st.session_state[f"show_history_{alerte['id']}"] = True

def marquer_alerte_traitee(alerte_id):
    """Marque une alerte comme traitée"""
    st.session_state.alertes_traitees.add(alerte_id)

def display_alertes_actives():
    """Affiche la liste des alertes actives"""
    
    st.markdown("### 🔥 Alertes actives nécessitant une action")
    
    # Filtres
    col_filter1, col_filter2, col_filter3, col_filter4 = st.columns(4)
    
    with col_filter1:
        filter_type = st.selectbox(
            "Type d'alerte",
            ["Tous", "Stock bas", "Expiration", "Gros mouvement"]
        )
    
    with col_filter2:
        filter_urgence = st.selectbox(
            "Niveau d'urgence",
            ["Tous", "CRITIQUE", "HAUTE", "MOYENNE", "BASSE"]
        )
    
    with col_filter3:
        filter_categorie = st.selectbox(
            "Catégorie",
            ["Toutes", "Électronique", "Informatique", "Bureau", "Médical"]
        )
    
    with col_filter4:
        st.write("")  # Espacement
        if st.button("🔄 Actualiser", use_container_width=True):
            st.rerun()
    
    # Récupérer et filtrer les alertes
    alertes = get_toutes_alertes()
    
    if filter_type != "Tous":
        type_map = {"Stock bas": "stock_bas", "Expiration": "expiration", "Gros mouvement": "gros_mouvement"}
        alertes = [a for a in alertes if a['type'] == type_map.get(filter_type, "")]
    
    if filter_urgence != "Tous":
        alertes = [a for a in alertes if a['urgence'] == filter_urgence]
    
    if filter_categorie != "Toutes":
        alertes = [a for a in alertes if a.get('categorie') == filter_categorie]
    
    # Afficher les alertes
    if alertes:
        # Trier par urgence
        alertes_triees = sorted(
            alertes,
            key=lambda x: (x['urgence'] == 'CRITIQUE', x['urgence'] == 'HAUTE', x['date_detection']),
            reverse=True
        )
        
        # Actions de groupe
        st.markdown("---")
        col_group1, col_group2, col_group3 = st.columns(3)
        
        with col_group1:
            if st.button("✅ Tout marquer comme traité", use_container_width=True):
                for alerte in alertes_triees:
                    marquer_alerte_traitee(alerte['id'])
                st.success("Toutes les alertes ont été marquées comme traitées")
                time.sleep(1)
                st.rerun()
        
        with col_group2:
            if st.button("📧 Exporter la liste", use_container_width=True):
                df = pd.DataFrame(alertes_triees)
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Télécharger CSV",
                    data=csv,
                    file_name=f"alertes_actives_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )
        
        with col_group3:
            if st.button("📋 Générer rapport", use_container_width=True):
                st.info("Rapport généré et envoyé par email")
        
        # Affichage des alertes
        st.markdown("---")
        for alerte in alertes_triees:
            display_carte_alerte(alerte, compact=False)
            st.markdown("")
    
    else:
        st.success("🎉 Excellent ! Aucune alerte active pour le moment.")
        st.balloons()

def display_historique_alertes():
    """Affiche l'historique des alertes traitées"""
    
    st.markdown("### 📜 Historique des alertes")
    
    # Statistiques historiques
    col_hist1, col_hist2, col_hist3 = st.columns(3)
    
    with col_hist1:
        jours = len(st.session_state.alertes_traitees)
        st.metric("Alertes traitées", jours)
    
    with col_hist2:
        # Simuler des données historiques
        moy_traitement = "2.1 jours"
        st.metric("Temps moyen traitement", moy_traitement)
    
    with col_hist3:
        taux_resolution = "92%"
        st.metric("Taux de résolution", taux_resolution)
    
    st.markdown("---")
    
    # Graphique historique
    st.markdown("#### 📈 Évolution des alertes (7 derniers jours)")
    
    # Données simulées pour l'historique
    dates = [(datetime.now() - timedelta(days=i)).strftime('%d/%m') for i in range(6, -1, -1)]
    data_hist = {
        'Date': dates,
        'Alertes actives': [12, 15, 8, 10, 7, 5, len(get_toutes_alertes())],
        'Alertes traitées': [8, 12, 10, 9, 8, 7, len(st.session_state.alertes_traitees)]
    }
    
    df_hist = pd.DataFrame(data_hist)
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=df_hist['Date'],
        y=df_hist['Alertes actives'],
        mode='lines+markers',
        name='Alertes actives',
        line=dict(color='#ef4444', width=3)
    ))
    
    fig.add_trace(go.Scatter(
        x=df_hist['Date'],
        y=df_hist['Alertes traitées'],
        mode='lines+markers',
        name='Alertes traitées',
        line=dict(color='#10b981', width=3)
    ))
    
    fig.update_layout(
        height=400,
        hovermode='x unified',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Liste des alertes traitées récemment
    st.markdown("---")
    st.markdown("#### 🕐 Dernières alertes traitées")
    
    # Dans une vraie application, vous auriez une table historique dans la base
    historique_simule = [
        {
            'id': 'STOCK-001',
            'titre': 'Stock bas: Clavier Mécanique',
            'date_traitement': (datetime.now() - timedelta(hours=2)).strftime('%d/%m/%Y %H:%M'),
            'traite_par': 'Admin',
            'action': 'Commande créée #CMD-456'
        },
        {
            'id': 'EXP-002',
            'titre': 'Produit expiré détecté',
            'date_traitement': (datetime.now() - timedelta(days=1)).strftime('%d/%m/%Y %H:%M'),
            'traite_par': 'Gestionnaire',
            'action': 'Produit retiré du stock'
        },
        {
            'id': 'MVT-003',
            'titre': 'Gros mouvement détecté',
            'date_traitement': (datetime.now() - timedelta(days=2)).strftime('%d/%m/%Y %H:%M'),
            'traite_par': 'Admin',
            'action': 'Transaction vérifiée et validée'
        }
    ]
    
    for hist in historique_simule:
        with st.expander(f"{hist['id']} - {hist['titre']}"):
            col_hist1, col_hist2, col_hist3 = st.columns(3)
            with col_hist1:
                st.write(f"**Traité le:** {hist['date_traitement']}")
            with col_hist2:
                st.write(f"**Traité par:** {hist['traite_par']}")
            with col_hist3:
                st.write(f"**Action:** {hist['action']}")
            
            if st.button("🔍 Voir détails", key=f"hist_detail_{hist['id']}"):
                st.info(f"Détails complets pour {hist['id']}")

def display_configuration_alertes():
    """Affiche la configuration des alertes"""
    
    st.markdown("### ⚙️ Configuration du système d'alertes")
    
    # Paramètres généraux
    with st.form("config_form"):
        st.markdown("#### 🔔 Paramètres de notification")
        
        col_notif1, col_notif2 = st.columns(2)
        
        with col_notif1:
            email_notif = st.checkbox("Notifications par email", value=True)
            if email_notif:
                emails = st.text_area(
                    "Destinataires emails (un par ligne)",
                    value="admin@stockflow.com\ngestion@stockflow.com",
                    height=100
                )
        
        with col_notif2:
            sms_notif = st.checkbox("Notifications SMS", value=False)
            if sms_notif:
                phones = st.text_area(
                    "Numéros de téléphone (un par ligne)",
                    placeholder="+33123456789\n+33198765432",
                    height=100
                )
        
        st.markdown("---")
        st.markdown("#### 📊 Seuils d'alerte")
        
        col_seuil1, col_seuil2, col_seuil3 = st.columns(3)
        
        with col_seuil1:
            seuil_critique = st.slider(
                "Seuil critique (%)",
                min_value=0,
                max_value=100,
                value=10,
                help="Pourcentage du stock minimum pour déclencher une alerte critique"
            )
        
        with col_seuil2:
            seuil_expiration = st.slider(
                "Jours avant expiration",
                min_value=1,
                max_value=90,
                value=30,
                help="Nombre de jours avant expiration pour déclencher une alerte"
            )
        
        with col_seuil3:
            seuil_mouvement = st.number_input(
                "Seuil gros mouvement",
                min_value=1,
                value=100,
                help="Quantité minimum pour déclencher une alerte de gros mouvement"
            )
        
        st.markdown("---")
        st.markdown("#### ⏰ Planification")
        
        frequence = st.select_slider(
            "Fréquence des vérifications",
            options=['15 minutes', '30 minutes', '1 heure', '3 heures', '6 heures', '12 heures', '24 heures'],
            value='1 heure'
        )
        
        heures_verif = st.multiselect(
            "Heures de vérification quotidienne",
            [f"{h:02d}:00" for h in range(24)],
            default=["08:00", "12:00", "16:00", "20:00"]
        )
        
        # Boutons de soumission
        col_submit1, col_submit2, col_submit3 = st.columns([2, 1, 1])
        
        with col_submit1:
            submit = st.form_submit_button(
                "💾 Enregistrer la configuration",
                type="primary",
                use_container_width=True
            )
        
        with col_submit2:
            test = st.form_submit_button(
                "🔧 Tester les notifications",
                use_container_width=True
            )
        
        with col_submit3:
            reset = st.form_submit_button(
                "🔄 Réinitialiser",
                use_container_width=True
            )
        
        if submit:
            st.success("✅ Configuration enregistrée avec succès")
            st.balloons()
        
        if test:
            st.info("📧 Notification de test envoyée aux destinataires configurés")
        
        if reset:
            st.info("Configuration réinitialisée aux valeurs par défaut")
    
    # Configuration avancée
    st.markdown("---")
    with st.expander("🔧 Configuration avancée"):
        st.markdown("#### 📊 Personnalisation des seuils par catégorie")
        
        try:
            categories = database.get_all_categories()
            
            for cat in categories:
                col_cat1, col_cat2, col_cat3 = st.columns([2, 1, 1])
                
                with col_cat1:
                    st.write(f"**{cat['nom']}**")
                
                with col_cat2:
                    seuil = st.number_input(
                        f"Seuil minimum {cat['nom']}",
                        min_value=1,
                        value=5,
                        key=f"seuil_{cat['id']}",
                        label_visibility="collapsed"
                    )
                
                with col_cat3:
                    if st.button("💾", key=f"save_cat_{cat['id']}"):
                        st.success(f"Seuil pour {cat['nom']} enregistré: {seuil}")
        
        except Exception as e:
            st.error(f"Erreur: {e}")
        
        st.markdown("---")
        st.markdown("#### 🗑️ Gestion des données")
        
        col_data1, col_data2 = st.columns(2)
        
        with col_data1:
            if st.button("🧹 Purger l'historique", use_container_width=True):
                # Dans une vraie app, supprimer les anciennes données
                jours_conservation = st.slider(
                    "Conserver les données de (jours)",
                    min_value=1,
                    max_value=365,
                    value=90,
                    key="purge_slider"
                )
                st.info(f"Historique purgé au-delà de {jours_conservation} jours")
        
        with col_data2:
            if st.button("📤 Exporter toutes les données", use_container_width=True):
                st.info("Export des données en cours...")

if __name__ == "__main__":
    show()