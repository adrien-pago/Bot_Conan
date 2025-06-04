# Bot Conan Exiles

Un bot Discord pour gérer et surveiller un serveur Conan Exiles.

## Fonctionnalités

- Suivi des kills et des morts des joueurs
- Suivi des constructions en cours
- Suivi des joueurs connectés
- Suivi des clans et de leurs statistiques
- Commandes Discord pour interagir avec le serveur
- Notifications automatiques pour les événements importants
- Gestion des votes des joueurs
- Limite de construction pour les bâtiments
- Gestion des objets et des inventaires

## Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/votre-username/Bot_Conan.git
cd Bot_Conan
```

2. Installez les dépendances :
```bash
pip install -r requirements.txt
```

3. Créez un fichier `.env` à la racine du projet avec les variables suivantes :
```env
# Discord
DISCORD_TOKEN=votre_token_discord
PLAYER_CHANNEL_ID=id_du_canal_joueurs
KILL_CHANNEL_ID=id_du_canal_kills
BUILD_CHANNEL_ID=id_du_canal_constructions
CLAN_CHANNEL_ID=id_du_canal_clans

# FTP
FTP_HOST=adresse_du_serveur_ftp
FTP_USER=utilisateur_ftp
FTP_PASSWORD=mot_de_passe_ftp
FTP_DB_PATH=chemin_vers_la_base_de_donnees

# RCON
RCON_HOST=adresse_du_serveur_rcon
RCON_PORT=port_rcon
RCON_PASSWORD=mot_de_passe_rcon
```

4. Lancez le bot :
```bash
python bot.py
```

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

## Structure du Projet

```
Bot_Conan/
├── bot.py                       # Point d'entrée principal du bot
├── bot_conan.service            # Configuration du service systemd
├── deploy.ps1                   # Script PowerShell pour le déploiement
├── requirements.txt             # Liste des dépendances Python
├── discord.db                   # Base de données SQLite pour Discord
├── .env                         # Variables d'environnement (à créer)
├── .gitignore                   # Fichiers ignorés par git
├── pyrightconfig.json           # Configuration pour Pyright (linter)
│
├── config/                      # Configuration du bot
│   ├── __init__.py             # Initialisation du package
│   ├── settings.py             # Paramètres généraux du bot
│   └── logging_config.py       # Configuration des logs
│
├── core/                        # Composants principaux
│   ├── __init__.py             # Initialisation du package
│   ├── bot_core.py             # Classe principale du bot
│   └── commands.py             # Gestion des commandes Discord
│
├── database/                    # Gestion de la base de données
│   ├── __init__.py             # Initialisation du package
│   ├── database_sync.py        # Synchronisation des données
│   ├── database_classement.py  # Gestion du classement des joueurs
│   ├── database_build.py       # Gestion des constructions
│   ├── create_items_table.py   # Création des tables d'objets
│   └── init_database.py        # Initialisation de la BDD
│
├── features/                    # Fonctionnalités du bot
│   ├── __init__.py             # Initialisation du package
│   ├── build_limit.py          # Limitation des constructions
│   ├── classement_player.py    # Système de classement des joueurs
│   ├── item_manager.py         # Gestion des objets in-game
│   ├── player_sync.py          # Synchronisation des données joueurs
│   ├── player_tracker.py       # Suivi des activités des joueurs
│   └── vote_tracker.py         # Système de votes
│
├── utils/                       # Utilitaires
│   ├── __init__.py             # Initialisation du package
│   ├── rcon_client.py          # Client RCON pour communiquer avec le serveur
│   ├── ftp_handler.py          # Gestion des connections FTP
│   └── helpers.py              # Fonctions utilitaires diverses
│
├── logs/                        # Dossier contenant les fichiers logs
│
├── Deploy-files/                # Fichiers pour le déploiement
│   ├── config/                 # Config pour déploiement
│   ├── core/                   # Core pour déploiement
│   ├── database/               # Database pour déploiement
│   ├── features/               # Features pour déploiement
│   ├── logs/                   # Logs pour déploiement
│   └── utils/                  # Utils pour déploiement
│
└── Tests/                       # Tests unitaires et d'intégration
```

## Commandes Discord

- `!aide` : Affiche l'aide pour les commandes disponibles
- `!stats` : Affiche les statistiques de kills
- `!builds` : Affiche les constructions en cours
- `!players` : Affiche la liste des joueurs connectés
- `!clans` : Affiche les statistiques des clans
- `!vote` : Système de vote pour les joueurs
- `!item` : Gestion des objets et inventaires

## Fonctionnalités Automatiques

- Mise à jour automatique du nom du canal avec le nombre de joueurs connectés
- Notifications des nouveaux kills
- Notifications des constructions terminées
- Suivi de l'activité des joueurs et des clans
- Sauvegarde automatique des statistiques
- Synchronisation avec la base de données du serveur Conan Exiles
- Limitations des constructions pour les joueurs
- Gestion des objets spéciaux et starter packs

## Base de données

Le bot utilise SQLite pour stocker les informations :
- `discord.db` : Stocke les données liées à Discord et aux joueurs
- Tables principales :
  - `users` : Informations sur les joueurs
  - `classement` : Classement des joueurs
  - `items` : Objets du jeu

## Notes Techniques



## Sécurité

- Ne partagez jamais votre fichier `.env`
- Assurez-vous que votre token Discord est sécurisé
- Utilisez des mots de passe forts pour le RCON
- Le fichier `.env` est ignoré par git (dans .gitignore)

## Contribution

Les contributions sont les bienvenues ! N'hésitez pas à ouvrir une issue ou à soumettre une pull request.

## Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

inventory type 0= inventaire 2= bare en bas
