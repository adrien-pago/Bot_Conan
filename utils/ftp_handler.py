import logging
import ftplib
import os
import tempfile
from config.logging_config import setup_logging
from config.settings import *
from dotenv import load_dotenv
from io import BytesIO
import threading

load_dotenv()

logger = setup_logging()

class FTPHandler:
    def __init__(self):
        """Initialise la connexion FTP"""
        self.host = os.getenv('FTP_HOST')
        self.port = int(os.getenv('FTP_PORT', '21'))
        self.user = os.getenv('FTP_USERNAME')
        self.password = os.getenv('FTP_PASSWORD')
        self.remote_path = os.getenv('FTP_REMOTE_PATH', 'ConanSandbox/Saved')
        
        if not all([self.host, self.user, self.password]):
            raise ValueError("Informations de connexion FTP manquantes dans le fichier .env")
        
        self.ftp = None
        self.max_retries = 3
        self.retry_delay = 5  # secondes
        self._lock = threading.Lock()

    def _connect(self):
        """Établit la connexion FTP avec gestion des erreurs"""
        with self._lock:
            for attempt in range(self.max_retries):
                try:
                    if self.ftp:
                        try:
                            self.ftp.quit()
                        except:
                            pass
                    
                    self.ftp = ftplib.FTP()
                    self.ftp.connect(self.host, self.port, timeout=10)
                    self.ftp.login(self.user, self.password)
                    logger.info("Connexion FTP établie avec succès")
                    return
                except Exception as e:
                    logger.error(f"Tentative {attempt + 1}/{self.max_retries} - Erreur lors de la connexion FTP: {e}")
                    if attempt < self.max_retries - 1:
                        import time
                        time.sleep(self.retry_delay)
                    else:
                        logger.error("Impossible de se connecter au serveur FTP après plusieurs tentatives")
                        raise

    def test_connection(self) -> bool:
        """Teste la connexion FTP"""
        try:
            self._connect()
            self.ftp.quit()
            return True
        except Exception as e:
            logger.error(f"❌ FTP connexion échouée : {e}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        try:
            self._connect()
            with open(local_path, 'wb') as f:
                self.ftp.retrbinary(f'RETR {remote_path}', f.write)
            self.ftp.quit()
            return True
        except Exception as e:
            logger.error(f"❌ Erreur download_file: {e}")
            return False

    def read_database(self, file_path):
        """Lit un fichier de la base de données via FTP"""
        try:
            # Se connecter au serveur FTP
            self._connect()
            
            # Créer un buffer en mémoire pour stocker les données
            buffer = BytesIO()
            
            # Télécharger le fichier
            self.ftp.retrbinary(f'RETR {file_path}', buffer.write)
            
            # Retourner le contenu du buffer
            return buffer.getvalue()
            
        except Exception as e:
            logger.error(f"Erreur lors de la lecture de la base de données: {e}")
            return None
        finally:
            self.close()

    def write_database(self, file_path, data):
        """Écrit un fichier dans la base de données via FTP"""
        try:
            # Se connecter au serveur FTP
            self._connect()
            
            # Créer un buffer en mémoire avec les données
            buffer = BytesIO(data)
            
            # Envoyer le fichier avec storbinary
            self.ftp.storbinary(f'STOR {file_path}', buffer)
            
            logger.info(f"Fichier {file_path} écrit avec succès")
            return True
            
        except Exception as e:
            logger.error(f"Erreur lors de l'écriture de la base de données: {e}")
            return False
        finally:
            self.close()

    def get_directory_structure(self, path: str = '/') -> dict:
        """Récupère la structure des répertoires"""
        self._connect()
        def _walk(cur_path):
            self.ftp.cwd(cur_path)
            entries = []
            self.ftp.retrlines('LIST', entries.append)
            tree = {}
            for line in entries:
                parts = line.split()
                name = parts[-1]
                if line.startswith('d'):
                    tree[name] = _walk(cur_path + '/' + name)
                else:
                    size = parts[4]
                    tree[name] = f"{size} bytes"
            self.ftp.cwd('..')
            return tree
        struct = _walk(path)
        self.ftp.quit()
        return struct

    def close(self):
        """Ferme la connexion FTP"""
        if self.ftp:
            try:
                self.ftp.quit()
                logger.info("Connexion FTP fermée")
            except:
                pass
            finally:
                self.ftp = None

    def upload_file(self, local_path, remote_path):
        """Envoie un fichier vers le serveur FTP"""
        try:
            self._connect()
            with open(local_path, 'rb') as f:
                self.ftp.storbinary(f'STOR {remote_path}', f)
            self.ftp.quit()
            logger.info(f"Fichier {local_path} envoyé avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi du fichier {local_path}: {e}")
            return False
            
    def list_files(self, remote_path='.'):
        """Liste les fichiers dans un répertoire FTP"""
        try:
            self._connect()
            files = []
            self.ftp.retrlines(f'LIST {remote_path}', lambda x: files.append(x.split()[-1]))
            self.ftp.quit()
            return files
        except Exception as e:
            logger.error(f"Erreur lors de la liste des fichiers dans {remote_path}: {e}")
            return []
            
    def create_directory(self, remote_path):
        """Crée un répertoire sur le serveur FTP"""
        try:
            self._connect()
            self.ftp.mkd(remote_path)
            self.ftp.quit()
            logger.info(f"Répertoire {remote_path} créé avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la création du répertoire {remote_path}: {e}")
            return False
            
    def delete_file(self, remote_path):
        """Supprime un fichier sur le serveur FTP"""
        try:
            self._connect()
            self.ftp.delete(remote_path)
            self.ftp.quit()
            logger.info(f"Fichier {remote_path} supprimé avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de la suppression du fichier {remote_path}: {e}")
            return False
            
    def rename_file(self, old_name, new_name):
        """Renomme un fichier sur le serveur FTP"""
        try:
            self._connect()
            self.ftp.rename(old_name, new_name)
            self.ftp.quit()
            logger.info(f"Fichier {old_name} renommé en {new_name} avec succès")
            return True
        except Exception as e:
            logger.error(f"Erreur lors du renommage du fichier {old_name}: {e}")
            return False
            
    def get_file_size(self, remote_path):
        """Récupère la taille d'un fichier sur le serveur FTP"""
        try:
            self._connect()
            size = self.ftp.size(remote_path)
            self.ftp.quit()
            return size
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la taille du fichier {remote_path}: {e}")
            return None
            
    def get_file_modification_time(self, remote_path):
        """Récupère la date de modification d'un fichier sur le serveur FTP"""
        try:
            self._connect()
            # Utiliser MDTM pour obtenir la date de modification
            response = self.ftp.sendcmd(f'MDTM {remote_path}')
            self.ftp.quit()
            if response.startswith('213'):
                # Format: 213 YYYYMMDDHHMMSS
                timestamp = response[4:].strip()
                return timestamp
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération de la date de modification du fichier {remote_path}: {e}")
            return None 