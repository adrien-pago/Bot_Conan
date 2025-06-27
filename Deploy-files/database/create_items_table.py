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
            #  Outils 
            (1, "Piolet stellaire", 51020, 10, 1, 100, 0, "Outils", 1),
            (2, "Couteau stellaire", 51312, 11, 1, 100, 0, "Outils", 1),
            (3, "Pioche stellaire", 51023, 12, 1, 100, 0, "Outils", 1),
            (4, "Faucille metal stellaire", 51042, 13, 1, 100, 0, "Outils", 1),
            (5, "Tranchoir metal stellaire", 41030, 14, 1, 100, 0, "Outils", 1),
            (6, "Massue du Tigre (légendaire)", 10095, 15, 1, 1000, 0, "Outils", 1),
            (7, "Natte mortuaire (légendaire)", 10096, 16, 1, 1000,0, "Outils", 1),
            
            # Ressources
            (8, "Brique", 16011, 103, 1000, 200, 0, "Ressources", 1),
            (9, "Brique durci", 16012, 104, 1000, 300, 0, "Ressources", 1),
            (10, "Renfort Fer", 16002, 105, 500, 300, 0, "Ressources", 1),
            (11, "Renfort Acier", 16003, 106, 500, 500, 0, "Ressources", 1),
            (12, "Feu d'acier", 14173, 107, 500, 500, 0, "Ressources", 1),
            (13, "Lingot Acier", 11502, 108, 100, 300, 0, "Ressources", 1),
            (14, "Lingot Acier renforcé", 18062, 109, 100, 500, 0, "Ressources", 1),
            (15, "Base Alchimie", 11070, 110, 1000, 500, 0, "Ressources", 1),
            (16, "Bois isolé", 11108, 111, 1000, 500, 0, "Ressources", 1),
            (17, "Bois façoné", 16021, 112, 1000, 500, 0, "Ressources", 1),

            #  Pets
            (18, "Cheval", 92226, 300, 1,  200, 0, "Pets", 1),
            (19, "Selle légère", 2708, 301, 1,  50, 0, "Pets", 1),

            #  Alchimie
            (20, "Extrait d'aoles", 53002, 200, 10, 200, 0, "Alchimie", 1),
            (21, "Extrait d'aoles pure", 53003, 201, 10, 500, 0, "Alchimie", 1),
            (22, "Antidote", 53503, 202, 10, 200, 0, "Alchimie", 1),
            (23, "Elexir de vigueur", 18299, 203, 10, 500, 0, "Alchimie", 1),
            (24, "Elexir de puissance", 18297, 204, 10, 500, 0, "Alchimie", 1),
            (25, "Elexir de grâce", 18290, 205, 10, 500, 0, "Alchimie", 1),
            (26, "Élixir de renaissance", 43015, 206, 20, 500, 0, "Alchimie",1),
            (27, "Élixir d'engourdissement", 18292, 207, 10, 500, 0, "Alchimie",1),
            (28, "Festin de Yog", 18212, 208, 50, 500, 0, "Alchimie",1),
            (29, "Poison du faucheur", 53201, 209, 10, 150, 0, "Alchimie",1),
            (30, "Poison de la reine scorpion", 53203, 210, 10, 300, 0, "Alchimie",1),
            (31, "Potion de mémoire bestiale", 19503, 211, 1, 10, 0, "Alchimie",1),
            (32, "Potion d'apprentissage naturel", 19504, 212, 1, 10, 0, "Alchimie",1),
            (33, "Potion de respiration", 53102, 213, 10, 200, 0, "Alchimie",1),
           
            #  Recipe
            (34, "Parchemin Atours Bestiaux", 10067, 607, 1, 3000, 0, "Recipe", 1),
            (35, "Parchemin Esclavagiste Khitan", 10104, 608, 1, 1000,0, "Recipe", 1),
            (36, "Parchemin Tenue de la Cour Guerrière", 95552, 609, 1, 2000,0, "Recipe", 1),

            # Thrall

            # Atelier
            (37, "Salle des cartes", 90000, 700, 1, 500, 0, "Atelier", 1),
            (38, "Jardinière T3", 18522, 701, 1, 500, 0, "Atelier", 1),
            (39, "Chaudron à creuset T3", 18552, 702, 1, 500, 0, "Atelier", 1),
            (40, "Établi d'alchimie T3", 18556, 703, 1, 500, 0, "Atelier", 1),
            (41, "Petite roue de la souffrance T1", 89911, 704, 1, 200, 0, "Atelier", 1),
            (42, "Grande roue de la souffrance T3", 89913, 705, 1, 600, 0, "Atelier", 1),
            (43, "Enclos T3", 51018, 706, 1, 300, 0,"Atelier",1),
            (44, "Fourneau T3", 18541, 707, 1, 500, 0,"Atelier",1),
            (45, "Tannerie T3", 18547, 708, 1, 500, 0,"Atelier",1),
            (46, "Armurie T3", 18546, 709, 1, 500, 0,"Atelier",1),
            (47, "Forgeron T3", 18544, 710, 1, 500, 0,"Atelier",1),
            (48, "Établi charpentier T3", 18549, 711, 1, 500, 0, "Atelier",1),
            (49, "Pupitre", 1587, 712, 10, 50, 0, "Atelier",1),
            (50, "Piège explosif", 80915, 714, 10, 1000, 0, "Atelier",1),
            (51, "Piège en fer à jambes", 80911, 715, 10, 1000, 0, "Atelier",1),
            (52, "Frigo amélioré", 18508, 716, 1, 100, 0, "Atelier",1),
            (53, "Ustensiles de guerre ingénieux", 11137, 717, 10, 500 , 0, "Atelier",1),

            #Sorcellery 
            (54, "Essence d'âme", 43014, 718, 20, 250, 0, "Sorcellery",1),
            (55, "Sang de sacrifié", 42001, 719, 10, 250, 0,"Sorcellery",1),
            (56, "Cristal de sang", 10027, 720, 50, 200, 0,"Sorcellery",1),
            (57, "Croc noueux", 10029, 721, 100, 1500, 0, "Sorcellery",1),
            (58, "Obole ancienne", 10025, 722, 500, 1500, 0,"Sorcellery",1),
            (59, "Pierre de téléportation (sorcellerie)", 19645, 713, 1, 500, 0,"Sorcellery",1),


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