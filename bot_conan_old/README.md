# Bot Discord Conan

Ce bot Discord est conçu pour intéragir avec un serveur Conan Exiles. Il permet de :
- Afficher le nombre de joueurs en ligne
- Gérer les constructions des clans
- Mettre à jour automatiquement un salon avec les informations du serveur

## Configuration

1. Installez les dépendances :
```bash
pip install -r requirements.txt
```

2. Configurez le fichier `.env` avec vos informations :
- `DISCORD_TOKEN` : Token de votre bot Discord
- `GAME_SERVER_HOST` : Adresse du serveur Conan Exiles
- `RCON_PORT` : Port RCON du serveur
- `RCON_PASSWORD` : Mot de passe RCON
- `TEST_CHANNEL_ID` : ID du salon Discord à mettre à jour

## Commandes Discord disponibles

- `!build` : Affiche les informations sur les constructions des clans

## Structure du projet

- `bot.py` : Le bot principal
- `rcon.py` : Gestionnaire de connexion RCON
- `database.py` : Gestionnaire de la base de données SQLite
- `ftp_handler.py` : Gestionnaire de connexion FTP
- `.env` : Configuration des variables d'environnement
- `requirements.txt` : Dépendances du projet
- `bot_conan.service` : Fichier de service systemd pour le déploiement

## Déploiement sur VPS

Pour déployer le bot sur votre VPS :

1. Préparer les fichiers localement :
```powershell
./deploy.ps1
```

2. Copier sur le VPS :
```bash
scp -r Deploy-files/* root@votre_ip:/root/bot/bot_conan/
```

3. Sur le VPS, installer les dépendances :
```bash
apt update
apt install -y python3 python3-pip
pip3 install -r requirements.txt
```

4. Configurer le service systemd :
```bash
cp bot_conan.service /etc/systemd/system/
systemctl daemon-reload
systemctl start bot_conan
systemctl enable bot_conan
```

## Gestion du service

Pour gérer le bot sur votre VPS :

- Voir le statut :
```bash
systemctl status bot_conan
```

- Redémarrer le bot :
```bash
systemctl restart bot_conan
```

- Arrêter le bot :
```bash
systemctl stop bot_conan
```

- Voir les logs en temps réel :
```bash
journalctl -u bot_conan -f
```

## Sécurité

- Ne partagez jamais votre fichier `.env`
- Assurez-vous que votre token Discord est sécurisé
- Utilisez des mots de passe forts pour le RCON
- Le fichier `.env` est ignoré par git (dans .gitignore)

