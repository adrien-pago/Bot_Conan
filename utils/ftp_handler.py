import logging
import ftplib
import os
import tempfile
from config.logging_config import setup_logging
from config.settings import *

logger = setup_logging()

class FTPHandler:
    def __init__(self):
        self.host = FTP_HOST
        self.user = FTP_USER
        self.password = FTP_PASSWORD
        self.ftp = None
        
    def connect(self):
        """Établit une connexion FTP"""
        try:
            self.ftp = ftplib.FTP(self.host)
            self.ftp.login(self.user, self.password)
            logger.info("Connexion FTP établie avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la connexion FTP: {e}")
            return False
            
    def disconnect(self):
        """Ferme la connexion FTP"""
        try:
            if self.ftp:
                self.ftp.quit()
                self.ftp = None
                logger.info("Connexion FTP fermée")
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture de la connexion FTP: {e}")
            
    def download_file(self, remote_path, local_path=None):
        """Télécharge un fichier depuis le serveur FTP"""
        try:
            if not self.ftp:
                if not self.connect():
                    return None
                    
            if not local_path:
                # Créer un fichier temporaire
                temp_file = tempfile.NamedTemporaryFile(delete=False)
                local_path = temp_file.name
                temp_file.close()
                
            with open(local_path, 'wb') as f:
                self.ftp.retrbinary(f'RETR {remote_path}', f.write)
                
            logger.info(f"Fichier {remote_path} téléchargé avec succès")
            return local_path
            
        except Exception as e:
            logger.error(f"Erreur lors du téléchargement du fichier {remote_path}: {e}")
            return None
            
    def upload_file(self, local_path, remote_path):
        """Envoie un fichier vers le serveur FTP"""
        try:
            if not self.ftp:
                if not self.connect():
                    return False
                    
            with open(local_path, 'rb') as f:
                self.ftp.storbinary(f'STOR {remote_path}', f)
                
            logger.info(f"Fichier {local_path} envoyé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du fichier {local_path}: {e}")
            return False
            
    def list_files(self, remote_path='.'):
        """Liste les fichiers dans un répertoire FTP"""
        try:
            if not self.ftp:
                if not self.connect():
                    return []
                    
            files = []
            self.ftp.retrlines(f'LIST {remote_path}', lambda x: files.append(x.split()[-1]))
            return files
            
        except Exception as e:
            logger.error(f"Erreur lors de la liste des fichiers dans {remote_path}: {e}")
            return []
            
    def create_directory(self, remote_path):
        """Crée un répertoire sur le serveur FTP"""
        try:
            if not self.ftp:
                if not self.connect():
                    return False
                    
            self.ftp.mkd(remote_path)
            logger.info(f"Répertoire {remote_path} créé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la création du répertoire {remote_path}: {e}")
            return False
            
    def delete_file(self, remote_path):
        """Supprime un fichier sur le serveur FTP"""
        try:
            if not self.ftp:
                if not self.connect():
                    return False
                    
            self.ftp.delete(remote_path)
            logger.info(f"Fichier {remote_path} supprimé avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du fichier {remote_path}: {e}")
            return False
            
    def rename_file(self, old_name, new_name):
        """Renomme un fichier sur le serveur FTP"""
        try:
            if not self.ftp:
                if not self.connect():
                    return False
                    
            self.ftp.rename(old_name, new_name)
            logger.info(f"Fichier {old_name} renommé en {new_name} avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors du renommage du fichier {old_name}: {e}")
            return False
            
    def get_file_size(self, remote_path):
        """Récupère la taille d'un fichier sur le serveur FTP"""
        try:
            if not self.ftp:
                if not self.connect():
                    return None
                    
            size = self.ftp.size(remote_path)
            return size
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la taille du fichier {remote_path}: {e}")
            return None
            
    def get_file_modification_time(self, remote_path):
        """Récupère la date de modification d'un fichier sur le serveur FTP"""
        try:
            if not self.ftp:
                if not self.connect():
                    return None
                    
            # Utiliser MDTM pour obtenir la date de modification
            response = self.ftp.sendcmd(f'MDTM {remote_path}')
            if response.startswith('213'):
                # Format: 213 YYYYMMDDHHMMSS
                timestamp = response[4:].strip()
                return timestamp
            return None
            
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la date de modification du fichier {remote_path}: {e}")
            return None 