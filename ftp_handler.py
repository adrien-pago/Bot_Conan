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
        self.port = int(os.getenv('FTP_PORT', 21))  # Port par défaut 21
        self.remote_path = os.getenv('FTP_PATH', '/')

    def connect(self):
        """Établir la connexion au serveur FTP"""
        try:
            ftp = ftplib.FTP()
            ftp.connect(self.host, self.port)
            ftp.login(self.username, self.password)
            ftp.cwd(self.remote_path)
            return ftp
        except Exception as e:
            raise Exception(f"Erreur de connexion FTP : {str(e)}")

    def test_connection(self):
        """Teste la connexion au serveur FTP"""
        try:
            ftp = self.connect()
            ftp.quit()
            return True
        except Exception as e:
            print(f"Erreur de connexion FTP : {str(e)}")
            return False
