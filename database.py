import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

class DatabaseManager:
    def __init__(self):
        """Initialisation du gestionnaire de base de données"""
        # Le chemin complet sur le serveur FTP est dans FTP_PATH
        self.db_path = 'ConanSandbox/Saved/game.db'
        self.local_db_path = 'game.db.local'  # Chemin local avec un nom différent

    def download_database(self, ftp_handler):
        """Télécharge la base de données game.db depuis le FTP"""
        try:
            # Afficher un message de début
            print("\nTéléchargement de la base de données...")
            
            # Vérifier la connexion FTP
            if not ftp_handler.is_connected():
                print("Pas de connexion FTP active, tentative de connexion...")
                if not ftp_handler.connect():
                    print("❌ Échec de la connexion FTP")
                    return False
            else:
                print("✅ Connexion FTP active")
            
            # Changer de répertoire vers ConanSandbox/Saved
            try:
                ftp_handler.ftp.cwd('ConanSandbox/Saved')
                print("✅ Répertoire ConanSandbox/Saved trouvé")
            except Exception as e:
                print(f"❌ Impossible de changer de répertoire : {str(e)}")
                return False
            
            # Télécharger la base de données principale
            try:
                print(f"Téléchargement de game.db vers {self.local_db_path}...")
                with open(self.local_db_path, 'wb') as f:
                    ftp_handler.ftp.retrbinary('RETR game.db', f.write)
                print(f"✅ Téléchargement terminé")
            except Exception as e:
                print(f"❌ Erreur lors du téléchargement : {str(e)}")
                return False

            # Télécharger les fichiers WAL et SHM s'ils existent
            try:
                print("Téléchargement du fichier WAL...")
                with open(self.local_db_path + '-wal', 'wb') as f:
                    ftp_handler.ftp.retrbinary('RETR game.db-wal', f.write)
                print("✅ Fichier WAL téléchargé")
            except Exception as e:
                print(f"⚠️ Fichier WAL non trouvé : {str(e)}")

            try:
                print("Téléchargement du fichier SHM...")
                with open(self.local_db_path + '-shm', 'wb') as f:
                    ftp_handler.ftp.retrbinary('RETR game.db-shm', f.write)
                print("✅ Fichier SHM téléchargé")
            except Exception as e:
                print(f"⚠️ Fichier SHM non trouvé : {str(e)}")

            # Retourner au répertoire précédent
            ftp_handler.ftp.cwd('../..')
            
            return True
        except Exception as e:
            print(f"❌ Erreur lors du téléchargement : {str(e)}")
            return False

    def get_players_and_clans(self):
        """Récupère la liste des joueurs et leurs clans depuis la base de données"""
        try:
            # Connexion à la base de données
            conn = sqlite3.connect(self.local_db_path)
            cursor = conn.cursor()
            
            # Afficher d'abord la structure de la base de données
            print("\nStructure de la base de données:")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            print("Tables disponibles:")
            for table in tables:
                print(f"- {table[0]}")
                
                # Afficher les colonnes de la table
                cursor.execute(f"PRAGMA table_info({table[0]})")
                columns = cursor.fetchall()
                print("  Colonnes:")
                for col in columns:
                    print(f"  - {col[1]} ({col[2]})")
            
            # Requête pour obtenir les joueurs et leurs clans
            # Ici nous devrons adapter la requête une fois que nous aurons vu la structure réelle
            cursor.execute("""
                SELECT 
                    pc.Name as PlayerName,
                    c.Name as ClanName
                FROM PlayerCharacter pc
                LEFT JOIN Clan c ON pc.ClanID = c.ClanID
                WHERE pc.Name IS NOT NULL AND pc.Name != ''
            """)
            
            results = cursor.fetchall()
            conn.close()
            return results
        except Exception as e:
            print(f"\nErreur lors de la lecture de la base de données : {str(e)}")
            conn.close()
            return []
