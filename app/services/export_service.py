# app/services/export_service.py - Service d'exportation de données
import pandas as pd
import json
import csv
import io
from datetime import datetime
from pathlib import Path
import logging
from models import database

logger = logging.getLogger(__name__)

# ============================================================================
# EXPORTATIONS STANDARD
# ============================================================================

def export_produits_csv():
    """Exporte tous les produits en CSV"""
    produits = database.get_all_produits()
    
    if not produits:
        raise ValueError("Aucun produit à exporter")
    
    df = pd.DataFrame(produits)
    
    # Sélection et ordre des colonnes
    columns_order = [
        'reference', 'nom', 'description', 'categorie_nom',
        'quantite', 'seuil_min', 'prix_achat', 'prix_vente',
        'fournisseur_nom', 'date_creation'
    ]
    
    # Filtrer les colonnes existantes
    existing_columns = [col for col in columns_order if col in df.columns]
    df_export = df[existing_columns].copy()
    
    # Formatage des dates
    if 'date_creation' in df_export.columns:
        df_export['date_creation'] = pd.to_datetime(df_export['date_creation']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Formatage des prix
    for col in ['prix_achat', 'prix_vente']:
        if col in df_export.columns:
            df_export[col] = df_export[col].apply(lambda x: f"{x:.2f}")
    
    # Créer le CSV en mémoire
    output = io.StringIO()
    df_export.to_csv(output, index=False, encoding='utf-8-sig', sep=';')
    
    return output.getvalue()

def export_produits_excel():
    """Exporte tous les produits en Excel avec onglets"""
    produits = database.get_all_produits()
    
    if not produits:
        raise ValueError("Aucun produit à exporter")
    
    # Créer un writer Excel
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # Onglet 1: Tous les produits
        df_all = pd.DataFrame(produits)
        
        # Colonnes principales
        main_columns = [
            'reference', 'nom', 'categorie_nom', 'quantite', 
            'seuil_min', 'prix_achat', 'prix_vente', 'fournisseur_nom'
        ]
        
        df_main = df_all[[col for col in main_columns if col in df_all.columns]].copy()
        df_main.to_excel(writer, sheet_name='Tous les produits', index=False)
        
        # Onglet 2: Produits en alerte
        produits_alerte = [p for p in produits if p['quantite'] <= p['seuil_min']]
        if produits_alerte:
            df_alerte = pd.DataFrame(produits_alerte)
            df_alerte[main_columns].to_excel(writer, sheet_name='Produits en alerte', index=False)
        
        # Onglet 3: Statistiques par catégorie
        if 'categorie_nom' in df_all.columns:
            stats = df_all.groupby('categorie_nom').agg({
                'reference': 'count',
                'quantite': 'sum',
                'prix_vente': lambda x: (x * df_all.loc[x.index, 'quantite']).sum()
            }).reset_index()
            
            stats.columns = ['Catégorie', 'Nombre produits', 'Total stock', 'Valeur totale']
            stats['Valeur totale'] = stats['Valeur totale'].round(2)
            stats.to_excel(writer, sheet_name='Stats par catégorie', index=False)
        
        # Onglet 4: Métadonnées
        metadata = pd.DataFrame({
            'Information': ['Date export', 'Nombre produits', 'Valeur stock totale'],
            'Valeur': [
                datetime.now().strftime('%Y-%m-%d %H:%M'),
                len(produits),
                f"{(df_all['quantite'] * df_all['prix_vente']).sum():.2f} DH"
            ]
        })
        metadata.to_excel(writer, sheet_name='Métadonnées', index=False)
    
    output.seek(0)
    return output.getvalue()

def export_mouvements_csv(filtres=None):
    """Exporte les mouvements de stock en CSV"""
    mouvements = database.get_mouvements(filtres)
    
    if not mouvements:
        raise ValueError("Aucun mouvement à exporter")
    
    df = pd.DataFrame(mouvements)
    
    # Formatage des colonnes
    if 'date_mouvement' in df.columns:
        df['date_mouvement'] = pd.to_datetime(df['date_mouvement']).dt.strftime('%Y-%m-%d %H:%M')
    
    # Ajouter une colonne Type français
    type_fr = {
        'entree': 'Entrée',
        'sortie': 'Sortie',
        'ajustement': 'Ajustement',
        'inventaire': 'Inventaire'
    }
    df['type_fr'] = df['type'].map(type_fr).fillna(df['type'])
    
    # Colonnes à exporter
    columns_export = [
        'date_mouvement', 'type_fr', 'produit_nom', 'quantite',
        'motif', 'utilisateur'
    ]
    
    existing_columns = [col for col in columns_export if col in df.columns]
    df_export = df[existing_columns].copy()
    
    # Renommer les colonnes
    rename_map = {
        'date_mouvement': 'Date',
        'type_fr': 'Type',
        'produit_nom': 'Produit',
        'quantite': 'Quantité',
        'motif': 'Motif',
        'utilisateur': 'Utilisateur'
    }
    df_export.rename(columns=rename_map, inplace=True)
    
    output = io.StringIO()
    df_export.to_csv(output, index=False, encoding='utf-8-sig', sep=';')
    
    return output.getvalue()

def export_rapport_complet():
    """Exporte un rapport complet en Excel avec plusieurs onglets"""
    # Récupérer toutes les données
    produits = database.get_all_produits()
    categories = database.get_all_categories()
    fournisseurs = database.get_all_fournisseurs()
    mouvements = database.get_mouvements({'limit': 1000})
    
    # Créer le fichier Excel
    output = io.BytesIO()
    
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # === ONGLET 1: PRODUITS ===
        if produits:
            df_produits = pd.DataFrame(produits)
            produits_columns = [
                'reference', 'nom', 'categorie_nom', 'quantite',
                'seuil_min', 'prix_achat', 'prix_vente', 'fournisseur_nom',
                'date_creation'
            ]
            
            existing_cols = [col for col in produits_columns if col in df_produits.columns]
            df_produits[existing_cols].to_excel(writer, sheet_name='Produits', index=False)
        
        # === ONGLET 2: STATISTIQUES ===
        stats_data = []
        
        # Statistiques générales
        stats = database.get_statistiques()
        for key, value in stats.items():
            stats_data.append([key.replace('_', ' ').title(), value])
        
        # Valeur par catégorie
        if produits:
            df_prod = pd.DataFrame(produits)
            if 'categorie_nom' in df_prod.columns:
                cat_stats = df_prod.groupby('categorie_nom').agg({
                    'id': 'count',
                    'quantite': 'sum',
                    'prix_vente': lambda x: (x * df_prod.loc[x.index, 'quantite']).sum()
                }).round(2)
                
                for cat, row in cat_stats.iterrows():
                    stats_data.append([f"Catégorie: {cat}", f"{row['id']} produits"])
                    stats_data.append([f"  Stock total", f"{row['quantite']} unités"])
                    stats_data.append([f"  Valeur", f"{row['prix_vente']:.2f} DH"])
        
        df_stats = pd.DataFrame(stats_data, columns=['Indicateur', 'Valeur'])
        df_stats.to_excel(writer, sheet_name='Statistiques', index=False)
        
        # === ONGLET 3: ALERTES ===
        if produits:
            produits_alerte = [p for p in produits if p['quantite'] <= p['seuil_min']]
            if produits_alerte:
                df_alerte = pd.DataFrame(produits_alerte)
                alerte_cols = ['reference', 'nom', 'categorie_nom', 'quantite', 'seuil_min']
                df_alerte[alerte_cols].to_excel(writer, sheet_name='Alertes', index=False)
        
        # === ONGLET 4: MOUVEMENTS RÉCENTS ===
        if mouvements:
            df_mouvements = pd.DataFrame(mouvements)
            if not df_mouvements.empty:
                mvt_cols = ['date_mouvement', 'type', 'produit_nom', 'quantite', 'motif']
                existing_mvt = [col for col in mvt_cols if col in df_mouvements.columns]
                df_mouvements[existing_mvt].to_excel(writer, sheet_name='Mouvements', index=False)
        
        # === ONGLET 5: SYNTHÈSE ===
        synthèse_data = [
            ['Rapport généré le', datetime.now().strftime('%Y-%m-%d %H:%M:%S')],
            ['Application', 'Gestion Stock Pro'],
            ['Nombre total de produits', len(produits) if produits else 0],
            ['Nombre de catégories', len(categories) if categories else 0],
            ['Nombre de fournisseurs', len(fournisseurs) if fournisseurs else 0],
            ['', ''],
            ['Produits en alerte', len(produits_alerte) if 'produits_alerte' in locals() else 0],
            ['Valeur stock totale', f"{(df_prod['quantite'] * df_prod['prix_vente']).sum():.2f} DH" 
             if produits and 'df_prod' in locals() else '0 DH']
        ]
        
        df_synthèse = pd.DataFrame(synthèse_data, columns=['Élément', 'Valeur'])
        df_synthèse.to_excel(writer, sheet_name='Synthèse', index=False)
    
    output.seek(0)
    return output.getvalue()

# ============================================================================
# EXPORTATIONS SPÉCIFIQUES
# ============================================================================

def export_inventaire_pdf_format():
    """Génère un format d'inventaire à imprimer"""
    produits = database.get_all_produits()
    
    if not produits:
        raise ValueError("Aucun produit pour l'inventaire")
    
    # Créer un DataFrame pour l'inventaire
    inventaire_data = []
    
    for produit in produits:
        inventaire_data.append({
            'Référence': produit.get('reference', ''),
            'Nom du produit': produit.get('nom', ''),
            'Catégorie': produit.get('categorie_nom', ''),
            'Emplacement': produit.get('emplacement', 'N/A'),
            'Stock théorique': produit.get('quantite', 0),
            'Stock physique': '',  # À remplir manuellement
            'Écart': '',  # Calculé après inventaire
            'Observations': ''
        })
    
    df = pd.DataFrame(inventaire_data)
    
    # Générer HTML pour impression
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Fiche d'Inventaire - {datetime.now().strftime('%d/%m/%Y')}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            h1 {{ color: #1E3A8A; border-bottom: 2px solid #3B82F6; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
            th {{ background-color: #1E3A8A; color: white; padding: 10px; text-align: left; }}
            td {{ border: 1px solid #ddd; padding: 8px; }}
            tr:nth-child(even) {{ background-color: #f2f2f2; }}
            .header {{ display: flex; justify-content: space-between; }}
            .info-box {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="header">
            <div>
                <h1>FICHE D'INVENTAIRE</h1>
                <p><strong>Date:</strong> {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
                <p><strong>Nombre de produits:</strong> {len(produits)}</p>
            </div>
            <div style="text-align: right;">
                <p><strong>Inventorié par:</strong> ________________</p>
                <p><strong>Validé par:</strong> ________________</p>
            </div>
        </div>
        
        <div class="info-box">
            <strong>Instructions:</strong><br>
            1. Comptez physiquement chaque produit<br>
            2. Notez la quantité réelle dans "Stock physique"<br>
            3. Calculez l'écart (Physique - Théorique)<br>
            4. Notez les observations (casse, erreur, etc.)
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Référence</th>
                    <th>Nom du produit</th>
                    <th>Catégorie</th>
                    <th>Emplacement</th>
                    <th>Stock théorique</th>
                    <th>Stock physique</th>
                    <th>Écart (+/-)</th>
                    <th>Observations</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for item in inventaire_data:
        html_content += f"""
                <tr>
                    <td>{item['Référence']}</td>
                    <td>{item['Nom du produit']}</td>
                    <td>{item['Catégorie']}</td>
                    <td>{item['Emplacement']}</td>
                    <td style="text-align: center;">{item['Stock théorique']}</td>
                    <td style="background-color: #e8f4fd;"></td>
                    <td style="background-color: #fff3cd;"></td>
                    <td style="background-color: #f8f9fa;"></td>
                </tr>
        """
    
    html_content += """
            </tbody>
        </table>
        
        <div style="margin-top: 30px; page-break-before: always;">
            <h2>Résumé de l'inventaire</h2>
            <table style="width: 50%;">
                <tr>
                    <td><strong>Total produits inventoriés:</strong></td>
                    <td>________________</td>
                </tr>
                <tr>
                    <td><strong>Écart total (unités):</strong></td>
                    <td>________________</td>
                </tr>
                <tr>
                    <td><strong>Valeur des écarts:</strong></td>
                    <td>________________ DH</td>
                </tr>
                <tr>
                    <td><strong>Date de clôture:</strong></td>
                    <td>________________</td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """
    
    return html_content

def export_alerte_stock_email_format():
    """Format pour envoi par email des alertes stock"""
    produits_alerte = database.get_produits_en_alerte()
    
    if not produits_alerte:
        raise ValueError("Aucune alerte de stock")
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; }}
            .alert {{ color: #856404; background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; border-radius: 5px; }}
            .header {{ background-color: #1E3A8A; color: white; padding: 20px; border-radius: 5px 5px 0 0; }}
            table {{ width: 100%; border-collapse: collapse; margin: 20px 0; }}
            th {{ background-color: #3B82F6; color: white; padding: 12px; text-align: left; }}
            td {{ border: 1px solid #ddd; padding: 10px; }}
            .urgent {{ background-color: #f8d7da; color: #721c24; }}
            .warning {{ background-color: #fff3cd; color: #856404; }}
            .footer {{ background-color: #f8f9fa; padding: 15px; border-radius: 0 0 5px 5px; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>ALERTE DE STOCK - {datetime.now().strftime('%d/%m/%Y')}</h1>
            <p>{len(produits_alerte)} produits nécessitent une attention immédiate</p>
        </div>
        
        <div class="alert">
            <strong>Action requise:</strong> Certains produits ont atteint ou sont en dessous de leur seuil minimum.
            Veuillez planifier un réapprovisionnement.
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Produit</th>
                    <th>Référence</th>
                    <th>Catégorie</th>
                    <th>Stock actuel</th>
                    <th>Seuil minimum</th>
                    <th>Écart</th>
                    <th>Fournisseur</th>
                </tr>
            </thead>
            <tbody>
    """
    
    for produit in produits_alerte:
        ecart = produit['quantite'] - produit['seuil_min']
        classe = "urgent" if produit['quantite'] == 0 else "warning"
        
        html_content += f"""
                <tr class="{classe}">
                    <td><strong>{produit['nom']}</strong></td>
                    <td>{produit.get('reference', 'N/A')}</td>
                    <td>{produit.get('categorie_nom', 'N/A')}</td>
                    <td style="text-align: center;"><strong>{produit['quantite']}</strong></td>
                    <td style="text-align: center;">{produit['seuil_min']}</td>
                    <td style="text-align: center;">{ecart}</td>
                    <td>{produit.get('fournisseur_nom', 'N/A')}</td>
                </tr>
        """
    
    html_content += f"""
            </tbody>
        </table>
        
        <div class="footer">
            <p><strong>Statistiques:</strong></p>
            <ul>
                <li>Produits en alerte: {len(produits_alerte)}</li>
                <li>Produits épuisés: {sum(1 for p in produits_alerte if p['quantite'] == 0)}</li>
                <li>Généré automatiquement par Gestion Stock Pro</li>
            </ul>
            <p style="font-size: 12px; color: #666; margin-top: 20px;">
                Ceci est une notification automatique. Merci de traiter ces alertes dans les plus brefs délais.
            </p>
        </div>
    </body>
    </html>
    """
    
    return html_content

# ============================================================================
# UTILITAIRES
# ============================================================================

def get_available_exports():
    """Retourne la liste des exports disponibles"""
    return {
        'produits_csv': {
            'name': '📄 Produits (CSV)',
            'description': 'Liste complète des produits au format CSV',
            'function': export_produits_csv,
            'filename': f'produits_{datetime.now().strftime("%Y%m%d")}.csv',
            'mime_type': 'text/csv'
        },
        'produits_excel': {
            'name': 'Produits (Excel)',
            'description': 'Rapport complet avec onglets au format Excel',
            'function': export_produits_excel,
            'filename': f'produits_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
            'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        },
        'mouvements_csv': {
            'name': 'Historique mouvements (CSV)',
            'description': 'Historique des entrées/sorties de stock',
            'function': lambda: export_mouvements_csv(),
            'filename': f'mouvements_{datetime.now().strftime("%Y%m%d")}.csv',
            'mime_type': 'text/csv'
        },
        'rapport_complet': {
            'name': 'Rapport complet (Excel)',
            'description': 'Rapport détaillé avec statistiques et alertes',
            'function': export_rapport_complet,
            'filename': f'rapport_stock_{datetime.now().strftime("%Y%m%d_%H%M")}.xlsx',
            'mime_type': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        },
        'fiche_inventaire': {
            'name': 'Fiche d\'inventaire (HTML)',
            'description': 'Format pour inventaire physique à imprimer',
            'function': export_inventaire_pdf_format,
            'filename': f'inventaire_{datetime.now().strftime("%Y%m%d")}.html',
            'mime_type': 'text/html'
        },
        'alertes_email': {
            'name': 'Alertes stock (HTML)',
            'description': 'Format pour envoi d\'alertes par email',
            'function': export_alerte_stock_email_format,
            'filename': f'alertes_stock_{datetime.now().strftime("%Y%m%d")}.html',
            'mime_type': 'text/html'
        }
    }

def generate_filename(base_name, extension):
    """Génère un nom de fichier avec timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base_name}_{timestamp}.{extension}"