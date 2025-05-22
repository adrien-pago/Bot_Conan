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
        self.remote_path = os.getenv('FTP_PATH', '/')

    def connect(self):
        """Établir la connexion au serveur FTP"""
        try:
            ftp = ftplib.FTP(self.host)
            ftp.login(self.username, self.password)
            ftp.cwd(self.remote_path)
            return ftp
        except Exception as e:
            raise Exception(f"Erreur de connexion FTP : {str(e)}")

    def get_data(self):
        """Récupérer les données depuis le FTP"""
        try:
            ftp = self.connect()
            files = ftp.nlst()
            data = []
            
            # Parcourir les fichiers et récupérer les informations
            for file in files:
                try:
                    # Ici vous devrez adapter selon le format de vos fichiers
                    # Par exemple si c'est du JSON
                    with open(file, 'r') as f:
                        content = json.load(f)
                        data.append(content)
                except Exception as e:
                    print(f"Erreur lors de la lecture de {file}: {str(e)}")
            
            ftp.quit()
            return data
        except Exception as e:
            raise Exception(f"Erreur lors de la récupération des données : {str(e)}")
