import os
import sys
import importlib
import sqlite3

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def init_database():
    """Initialise la base de données en créant toutes les tables nécessaires"""
    print("Initialisation de la base de données...")
    
    # Vérifier si la base de données existe, sinon la créer
    if not os.path.exists('discord.db'):
        print("Création de la base de données discord.db")
        conn = sqlite3.connect('discord.db')
        conn.close()
    
    # Importer et exécuter tous les scripts de création de tables
    try:
        # Importer le script de création des tables d'items
        from database.create_items_table import create_items_tables
        create_items_tables()
        
        # Ajouter ici d'autres scripts d'initialisation si nécessaire
        # from database.another_script import another_function
        # another_function()
        
        print("Base de données initialisée avec succès!")
        return True
    except Exception as e:
        print(f"Erreur lors de l'initialisation de la base de données: {e}")
        return False

if __name__ == "__main__":
    init_database() 