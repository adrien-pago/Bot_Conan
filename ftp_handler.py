import ftplib
import json
from dotenv import load_dotenv
import os

class FTPHandler:
    def __init__(self):
        """Initialisation du gestionnaire FTP"""
        load_dotenv()
        self.host = os.getenv('FTP_HOST')
        self.username = os.getenv('FTP_USERNAME')
        self.password = os.getenv('FTP_PASSWORD')
        self.port = int(os.getenv('FTP_PORT', 21))
        self.remote_path = os.getenv('FTP_PATH', '/')
        self.ftp = None
        
    def connect(self, path=None):
        """Établir la connexion au serveur FTP"""
        try:
            print(f"Connexion à {self.host}:{self.port} avec le chemin {self.remote_path}")
            
            if self.ftp:
                print("Déconnexion de la connexion précédente...")
                self.ftp.quit()
                self.ftp = None
            
            print("Tentative de connexion...")
            self.ftp = ftplib.FTP()
            self.ftp.connect(self.host, self.port)
            self.ftp.login(self.username, self.password)
            print("✅ Connexion réussie")
            
            if path:
                print(f"Changement de répertoire vers {path}")
                self.ftp.cwd(path)
            else:
                print(f"Changement de répertoire vers {self.remote_path}")
                self.ftp.cwd(self.remote_path)
            
            # Vérifier le contenu du répertoire ConanSandbox
            print("\nContenu du dossier ConanSandbox:")
            try:
                self.ftp.cwd('ConanSandbox')
                
                # Vérifier le contenu du dossier Saved
                print("\nContenu du dossier Saved:")
                try:
                    self.ftp.cwd('Saved')
                    self.ftp.dir()
                except Exception as e:
                    print(f"⚠️ Impossible d'accéder au dossier Saved : {str(e)}")
                
                # Retourner au répertoire précédent
                self.ftp.cwd('..')
            except Exception as e:
                print(f"⚠️ Impossible d'accéder au dossier ConanSandbox : {str(e)}")
            
            # Vérifier le contenu du répertoire actuel
            print("\nContenu du répertoire actuel:")
            self.ftp.dir()
            
            return self.ftp
        except Exception as e:
            print(f"❌ Erreur de connexion FTP : {str(e)}")
            self.ftp = None
            return None

    def download_file(self, remote_path, local_path):
        """Télécharger un fichier depuis le FTP"""
        try:
            if not self.ftp:
                if not self.connect():
                    return False
            
            with open(local_path, 'wb') as f:
                self.ftp.retrbinary(f'RETR {remote_path}', f.write)
            return True
        except Exception as e:
            print(f"Erreur lors du téléchargement : {str(e)}")
            return False

    def test_connection(self):
        """Teste la connexion au serveur FTP"""
        try:
            if not self.ftp:
                return self.connect()
            else:
                self.ftp.voidcmd("NOOP")  # Test simple de la connexion
                return True
        except Exception as e:
            print(f"Erreur de test de connexion : {str(e)}")
            self.ftp = None
            return False

    def test_connection(self):
        """Teste la connexion au serveur FTP"""
        try:
            ftp = self.connect()
            ftp.quit()
            return True
        except Exception as e:
            print(f"Erreur de connexion FTP : {str(e)}")
            return False

    def get_directory_structure(self, path='/', depth=0):
        """
        Récupère la structure des dossiers FTP
        Args:
            path: Chemin à analyser
            depth: Profondeur actuelle pour l'indentation
        Returns:
            dict: Structure des dossiers
        """
        try:
            ftp = self.connect(path)
            
            # Récupère la liste des fichiers et dossiers
            items = []
            ftp.dir(items.append)
            
            # Analyse les résultats
            structure = {}
            for item in items:
                # Parse la ligne de résultat du FTP
                parts = item.split()
                if len(parts) >= 9:
                    name = parts[-1]
                    is_dir = parts[0].startswith('d')
                    
                    # Pour les dossiers, on fait une récursion
                    if is_dir:
                        try:
                            # Vérifier d'abord si le dossier existe
                            ftp.cwd(name)
                            ftp.cwd('..')
                            structure[name] = self.get_directory_structure(path + '/' + name, depth + 1)
                        except ftplib.error_perm:
                            structure[name] = "[Accès refusé]"
                    else:
                        # Pour les fichiers, on récupère la taille
                        size = parts[4]
                        structure[name] = f"{size} bytes"
            
            ftp.quit()
            return structure
        except Exception as e:
            print(f"Erreur lors de la récupération de la structure : {str(e)}")
            return {}

    def test_connection(self):
        """Teste la connexion au serveur FTP"""
        try:
            ftp = self.connect()
            ftp.quit()
            return True
        except Exception as e:
            print(f"Erreur de connexion FTP : {str(e)}")
            return False

    def get_directory_structure(self, path='/', depth=0):
        """
        Récupère la structure des dossiers FTP
        Args:
            path: Chemin à analyser
            depth: Profondeur actuelle pour l'indentation
        Returns:
            dict: Structure des dossiers
        """
        try:
            ftp = self.connect()
            
            # Change le répertoire courant
            ftp.cwd(path)
            
            # Récupère la liste des fichiers et dossiers
            items = []
            ftp.dir(items.append)
            
            # Analyse les résultats
            structure = {}
            for item in items:
                # Parse la ligne de résultat du FTP
                parts = item.split()
                if len(parts) >= 9:
                    name = parts[-1]
                    is_dir = parts[0].startswith('d')
                    
                    # Pour les dossiers, on fait une récursion
                    if is_dir:
                        try:
                            structure[name] = self.get_directory_structure(path + '/' + name, depth + 1)
                        except ftplib.error_perm:
                            structure[name] = "[Accès refusé]"
                    else:
                        # Pour les fichiers, on récupère la taille
                        size = parts[4]
                        structure[name] = f"{size} bytes"
            
            ftp.quit()
            return structure
        except Exception as e:
            print(f"Erreur lors de la récupération de la structure : {str(e)}")
            return {}

    def get_player_info(self):
        """Récupère les informations des joueurs connectés depuis les logs"""
        try:
            ftp = self.connect()
            ftp.cwd('/Saved/Logs')
            
            # Récupérer le dernier fichier log
            files = []
            ftp.dir(files.append)
            
            # Trouver le fichier log le plus récent
            latest_log = None
            for line in files:
                parts = line.split()
                if 'ConanSandbox.log' in parts[-1]:
                    latest_log = parts[-1]
                    break
            
            if not latest_log:
                return "Aucun fichier log trouvé"
            
            # Télécharger le fichier
            with open('latest_log.txt', 'wb') as f:
                ftp.retrbinary(f'RETR {latest_log}', f.write)
            
            # Analyser le fichier pour trouver les joueurs connectés
            with open('latest_log.txt', 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            # Rechercher les joueurs connectés
            players = []
            for line in lines:
                if 'Player Login:' in line:
                    # Extraire le nom du joueur
                    parts = line.split('Player Login:')
                    if len(parts) > 1:
                        player_name = parts[1].strip()
                        players.append(player_name)
            
            ftp.quit()
            return players
            
        except Exception as e:
            print(f"Erreur lors de la récupération des informations des joueurs : {str(e)}")
            return []

    def get_clan_info(self):
        """Récupère les informations des clans depuis la base de données"""
        try:
            ftp = self.connect()
            ftp.cwd('/Saved')
            
            # Télécharger la base de données
            with open('game.db', 'wb') as f:
                ftp.retrbinary('RETR game.db', f.write)
            
            # Utiliser sqlite3 pour lire la base de données
            import sqlite3
            conn = sqlite3.connect('game.db')
            cursor = conn.cursor()
            
            # Requête pour obtenir les clans
            cursor.execute('''
                SELECT 
                    ClanName,
                    COUNT(*) as MemberCount
                FROM Clans
                GROUP BY ClanName
                ORDER BY MemberCount DESC
            ''')
            
            clans = cursor.fetchall()
            
            conn.close()
            ftp.quit()
            
            return clans
            
        except Exception as e:
            print(f"Erreur lors de la récupération des informations des clans : {str(e)}")
            return []
