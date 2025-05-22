import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        """Initialisation du gestionnaire de base de données"""
        self.db_path = 'bot_data.db'

    def create_table(self):
        """Créer la table pour stocker les données"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS data_entries (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    data TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()

    def insert_data(self, data):
        """Insérer les données dans la base"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for item in data:
                cursor.execute('''
                    INSERT INTO data_entries (data)
                    VALUES (?)
                ''', (json.dumps(item),))
            conn.commit()

    def get_stats(self):
        """Récupérer les statistiques"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Récupérer le nombre total d'entrées
            cursor.execute('SELECT COUNT(*) FROM data_entries')
            total = cursor.fetchone()[0]
            
            # Récupérer la dernière mise à jour
            cursor.execute('SELECT MAX(timestamp) FROM data_entries')
            last_update = cursor.fetchone()[0]
            
            return {
                'total': total,
                'last_update': last_update
            }
