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
            id_item_shop INTEGER NOT NULL,
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

        # Ajouter les items du shop si elles n'existent pas déjà
        shop_items = [
            (1, "Piolet stellaire", 51020, 100, 1, 100, 0, "Outils", 1),
            (2, "Couteau stellaire", 51312, 101, 1, 100, 0, "Outils", 1),
            (3, "Pioche stellaire", 51023, 102, 1, 100, 0, "Outils", 1),
            (4, "Brique", 16011, 103, 1000, 200, 0, "Ressources", 1),
            (5, "Brique durci", 16012, 104, 10000, 300, 0, "Ressources", 1),
            (6, "Renfort Fer", 16002, 105, 500, 300, 0, "Ressources", 1),
            (7, "Renfort Acier", 16003, 106, 500, 1000, 0, "Ressources", 1),
            (8, "Feu d'acier", 14173, 107, 500, 500, 0, "Ressources", 1),
            (9, "Lingot Acier", 11502, 108, 100, 200, 0, "Ressources", 1),
            (10, "Lingot Acier renforcé", 18062, 109, 100, 300, 0, "Ressources", 1),
            (11, "Base Alchimie", 11070, 110, 1000, 1000, 0, "Ressources", 1),
            (12, "Bois isolé", 11108, 111, 1000, 500, 0, "Ressources", 1),
            (13, "Bois façoné", 16021, 112, 1000, 500, 0, "Ressources", 1),
            (14, "Grande hache stellaire", 50492, 200, 1, 100, 0, "Armes", 1),
            (15, "Coffre en fer", 80852, 400 , 1,  100, 0, "Stockage", 1),
            (16, "Cheval", 92226, 300, 1,  300, 0, "Pets", 1),
            (17, "Selle légère", 2708, 301, 1,  50, 0, "Pets", 1),
            (18, "Extrait d'aoles", 53002, 200, 10, 200, 0, "Potions", 1),
            (19, "Extrait d'aoles pure", 53003, 201, 10, 500, 0, "Potions", 1),
            (20, "Antidote", 53503, 202, 10, 200, 0, "Potions", 1),
            (21, "Elexir de vigueur", 18299, 203, 10, 500, 0, "Potions", 1),
            (22, "Elexir de force", 18297, 204, 10, 500, 0, "Potions", 1),
            (23, "Elexir de grâce", 18290, 205, 10, 500, 0, "Potions", 1)
        ]

        # Vérifier si les items existent déjà
        cursor.execute("SELECT COUNT(*) FROM items")
        count = cursor.fetchone()[0]
        
        # Si la table est vide, ajouter les items du shop
        if count == 0:
            cursor.executemany('''
            INSERT INTO items (id, name, item_id, id_item_shop, count, price, cooldown, category, enabled)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', shop_items)
            print("Items du shop ajoutés avec succès!")
        
        conn.commit()
        print("Tables des items créées avec succès!")
        
    except Exception as e:
        print(f"Erreur lors de la création des tables: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    create_items_tables() 