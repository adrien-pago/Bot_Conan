# Bot Discord avec FTP et SQLite

Ce bot Discord permet de récupérer des informations depuis un serveur FTP et de les stocker dans une base de données SQLite.

## Configuration

1. Installez les dépendances :
```bash
pip install -r requirements.txt
```

2. Configurez le fichier `.env` avec vos informations :
- `DISCORD_TOKEN` : Token de votre bot Discord
- `FTP_HOST` : Adresse du serveur FTP
- `FTP_USERNAME` : Nom d'utilisateur FTP
- `FTP_PASSWORD` : Mot de passe FTP
- `FTP_PATH` : Chemin sur le serveur FTP (optionnel)

## Commandes disponibles

- `!afficher_info` : Affiche les informations récupérées depuis le FTP
- `!stats` : Affiche les statistiques de la base de données

## Structure du projet

- `bot.py` : Le bot principal
- `ftp_handler.py` : Gestionnaire de connexion FTP
- `database.py` : Gestionnaire de la base de données SQLite
- `.env` : Configuration des variables d'environnement
- `requirements.txt` : Dépendances du projet

## Sécurité

- Ne partagez jamais votre fichier `.env`
- Assurez-vous que votre token Discord est sécurisé
- Utilisez des mots de passe forts pour votre FTP
