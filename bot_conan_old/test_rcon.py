import socket
import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Récupérer les paramètres RCON
host = os.getenv('GAME_SERVER_HOST')
port = os.getenv('RCON_PORT')
password = os.getenv('RCON_PASSWORD')

# Afficher les paramètres
print("🔧 Paramètres RCON:")
print(f"  Host: {host}")
print(f"  Port: {port}")
print(f"  Password: {'*' * len(password) if password else 'Non défini'}")

# Vérifier si les paramètres sont définis
if not host:
    print("❌ ERREUR: GAME_SERVER_HOST n'est pas défini")
    exit(1)
if not port:
    print("❌ ERREUR: RCON_PORT n'est pas défini")
    exit(1)
if not password:
    print("❌ ERREUR: RCON_PASSWORD n'est pas défini")
    exit(1)

# Convertir le port en entier
try:
    port = int(port)
except ValueError:
    print(f"❌ ERREUR: RCON_PORT invalide: {port}")
    exit(1)

# Tester la connexion TCP
print(f"\n→ Test connexion TCP à {host}:{port}")
try:
    # Créer la connexion avec un timeout plus long
    s = socket.create_connection((host, port), timeout=10)
    print("✅ TCP OK")
    
    # Tester l'envoi du mot de passe
    print("→ Test authentification RCON")
    s.sendall((password + "\n").encode())
    
    # Lire la réponse
    response = s.recv(1024)
    print(f"Réponse du serveur: {response.decode('utf-8', errors='replace')}")
    
    s.close()
    print("✅ Test RCON complet réussi")
    
except socket.timeout:
    print("❌ ERREUR: Timeout de connexion")
except socket.error as e:
    print(f"❌ ERREUR: {e}")
except Exception as e:
    print(f"❌ ERREUR inattendue: {e}")

print("\nTest terminé")
