# Bot Discord avec FTP et SQLite

Ce bot Discord permet de récupérer des informations depuis un serveur FTP et de les stocker dans une base de données SQLite.

## Configuration

1. Installez les dépendances :
```bash
pip install -r requirements.txt
```

2. Configurez le fichier `.env` avec vos informations :
- `DISCORD_TOKEN` : Token de votre bot Discord
- `FTP_HOST` : Adresse du serveur FTP (ex: 176.57.178.12)
- `FTP_USERNAME` : Nom d'utilisateur FTP
- `FTP_PASSWORD` : Mot de passe FTP
- `FTP_PORT` : Port FTP (ex: 28321)
- `FTP_PATH` : Chemin sur le serveur FTP (optionnel)

## Commandes disponibles



## Structure du projet

- `bot.py` : Le bot principal
- `ftp_handler.py` : Gestionnaire de connexion FTP
- `database.py` : Gestionnaire de la base de données SQLite
- `.env` : Configuration des variables d'environnement
- `requirements.txt` : Dépendances du projet

## Sécurité

- Ne partagez jamais votre fichier `.env`
- Assurez-vous que votre token Discord est sécurisé
- Utilisez des mots de passe forts pour le FTP
- Le fichier `.env` est ignoré par git (dans .gitignore)

