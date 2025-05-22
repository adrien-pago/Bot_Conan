import sqlite3

def show_database_structure(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Afficher toutes les tables
    print("\nTables dans la base de données:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        print(f"\nTable: {table_name}")
        
        # Afficher les colonnes de la table
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        
        print("Colonnes:")
        for col in columns:
            print(f"- {col[1]} ({col[2]})")
        
        # Afficher les contraintes de la table
        cursor.execute(f"PRAGMA foreign_key_list({table_name});")
        foreign_keys = cursor.fetchall()
        
        if foreign_keys:
            print("\nContraintes de clé étrangère:")
            for fk in foreign_keys:
                print(f"- {fk[3]} -> {fk[2]}.{fk[4]}")
    
    conn.close()

# Utilisation
show_database_structure('game.db')