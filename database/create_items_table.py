import sqlite3
import os
import sys

# Ajouter le répertoire parent au PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def create_items_tables():
    """Crée les tables nécessaires pour la gestion des items si elles n'existent pas déjà"""
    try:
        conn = sqlite3.connect('discord.db')
        cursor = conn.cursor()

        # Créer la table des items
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            count INTEGER DEFAULT 1,
            price INTEGER DEFAULT 0,
            cooldown INTEGER DEFAULT 0,
            category TEXT,
            enabled INTEGER DEFAULT 1
        )
        ''')

        # Créer la table pour l'historique des transactions
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS item_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            discord_id TEXT NOT NULL,
            player_name TEXT NOT NULL,
            item_id INTEGER NOT NULL,
            count INTEGER DEFAULT 1,
            price INTEGER DEFAULT 0,
            status TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (item_id) REFERENCES items (id)
        )
        ''')

        # Ajouter les items du starter pack s'ils n'existent pas déjà
        starter_items = [
            (1, "Piolet stellaire", 51020, 1, 100, 0, "Outils", 1),
            (2, "couteau stellaire", 51312, 1, 100, 0, "Outils", 1),
            (3, "Grande hache stellaire", 50492, 1, 100, 0, "Armes", 1),
            (4, "Coffre en fer", 80852, 1, 100, 0, "Stockage", 1),
            (5, "Cheval", 92226, 1, 300, 0, "Pets", 1),
            (6, "Selle légère", 2708, 1, 50, 0, "Pets", 1),
            (7, "Extrait d'aoles", 53002, 1, 20, 0, "Potions", 1)
        ]

        # Vérifier si les items existent déjà
        cursor.execute("SELECT COUNT(*) FROM items")
        count = cursor.fetchone()[0]
        
        # Si la table est vide, ajouter les items du starter pack
        if count == 0:
            cursor.executemany('''
            INSERT INTO items (id, name, item_id, count, price, cooldown, category, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', starter_items)
            print("Items du starter pack ajoutés avec succès!")
        
        conn.commit()
        print("Tables des items créées avec succès!")
        
    except Exception as e:
        print(f"Erreur lors de la création des tables: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_items_tables() 