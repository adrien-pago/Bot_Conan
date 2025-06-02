# ftp_handler.py
import ftplib
import os
from dotenv import load_dotenv

load_dotenv()

class FTPHandler:
    def __init__(self):
        self.host     = os.getenv('FTP_HOST')
        self.port     = int(os.getenv('FTP_PORT', 21))
        self.user     = os.getenv('FTP_USERNAME')
        self.password = os.getenv('FTP_PASSWORD')

    def connect(self):
        ftp = ftplib.FTP()
        ftp.connect(self.host, self.port)
        ftp.login(self.user, self.password)
        return ftp

    def test_connection(self) -> bool:
        try:
            ftp = self.connect()
            ftp.quit()
            return True
        except Exception as e:
            print(f"❌ FTP connexion échouée : {e}")
            return False

    def download_file(self, remote_path: str, local_path: str) -> bool:
        try:
            ftp = self.connect()
            with open(local_path, 'wb') as f:
                ftp.retrbinary(f'RETR {remote_path}', f.write)
            ftp.quit()
            return True
        except Exception as e:
            print(f"❌ Erreur download_file: {e}")
            return False

    def read_database(self, remote_path: str) -> bytes:
        """Lire directement la base de données depuis le FTP sans la sauvegarder"""
        try:
            ftp = self.connect()
            # Créer un tampon mémoire pour stocker la base de données
            from io import BytesIO
            buffer = BytesIO()
            ftp.retrbinary(f'RETR {remote_path}', buffer.write)
            ftp.quit()
            return buffer.getvalue()
        except Exception as e:
            print(f"❌ Erreur lecture base de données: {e}")
            return None

    def get_directory_structure(self, path: str = '/') -> dict:
        ftp = self.connect()
        def _walk(cur_path):
            ftp.cwd(cur_path)
            entries = []
            ftp.retrlines('LIST', entries.append)
            tree = {}
            for line in entries:
                parts = line.split()
                name = parts[-1]
                if line.startswith('d'):
                    tree[name] = _walk(cur_path + '/' + name)
                else:
                    size = parts[4]
                    tree[name] = f"{size} bytes"
            ftp.cwd('..')
            return tree
        struct = _walk(path)
        ftp.quit()
        return struct
