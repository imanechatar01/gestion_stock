# app/services/produit_service.py - Service de gestion des produits
from models import database

def calculer_valeur_stock(produit_id):
    """Calcule la valeur du stock pour un produit"""
    produit = database.get_produit_by_id(produit_id)
    if produit:
        return produit['quantite'] * produit['prix_vente']
    return 0

def verifier_alerte_stock(produit_id):
    """Vérifie si un produit est en alerte de stock"""
    produit = database.get_produit_by_id(produit_id)
    if produit:
        return produit['quantite'] <= produit['seuil_min']
    return False

def get_produits_par_fournisseur(fournisseur_id):
    """Récupère tous les produits d'un fournisseur"""
    produits = database.get_all_produits()
    return [p for p in produits if p['fournisseur_id'] == fournisseur_id]