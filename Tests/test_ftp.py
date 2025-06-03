import os
import ftplib
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Récupérer les informations de connexion
host = os.getenv('FTP_HOST')
port = int(os.getenv('FTP_PORT', '21'))
user = os.getenv('FTP_USERNAME')
password = os.getenv('FTP_PASSWORD')
remote_path = os.getenv('FTP_REMOTE_PATH', 'ConanSandbox/Saved')
log_path = os.getenv('FTP_LOG_PATH', 'ConanSandbox/Saved/Logs/ConanSandbox.log')
game_db = os.getenv('FTP_GAME_DB', 'ConanSandbox/Saved/game.db')

print(f"Connexion à {host}:{port} avec {user}...")

# Se connecter au serveur FTP
ftp = ftplib.FTP()
ftp.connect(host, port)
ftp.login(user, password)
print("Connexion réussie!")

# Lister les dossiers à la racine
print("\nContenu de la racine:")
ftp.retrlines('LIST')

# Vérifier les chemins
paths_to_check = [
    remote_path,
    log_path,
    game_db
]

for path in paths_to_check:
    print(f"\nVérification du chemin: {path}")
    parts = path.split('/')
    current = ""
    success = True
    
    for part in parts:
        if not part:
            continue
        if current:
            current += "/"
        current += part
        
        try:
            # Essayer de changer de répertoire
            ftp.cwd(current if not current else "/"+current)
            print(f"✅ Répertoire trouvé: {current}")
            # Revenir à la racine
            ftp.cwd("/")
        except Exception as e:
            # Si c'est le dernier élément, essayer de vérifier si c'est un fichier
            if path.endswith(current):
                try:
                    # Essayer de lister le fichier
                    ftp.cwd("/")
                    size = ftp.size(current)
                    print(f"✅ Fichier trouvé: {current} (Taille: {size} octets)")
                except Exception as e:
                    print(f"❌ Fichier non trouvé: {current} - Erreur: {e}")
                    success = False
            else:
                print(f"❌ Répertoire non trouvé: {current} - Erreur: {e}")
                success = False
            break

    if success:
        print(f"✅ Chemin valide: {path}")
    else:
        print(f"❌ Chemin invalide: {path}")

# Fermer la connexion
ftp.quit()
