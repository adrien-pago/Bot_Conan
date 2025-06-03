# Bot Conan Exiles

Un bot Discord pour gérer et surveiller un serveur Conan Exiles.

## Fonctionnalités

- Suivi des kills et des morts des joueurs
- Suivi des constructions en cours
- Suivi des joueurs connectés
- Suivi des clans et de leurs statistiques
- Commandes Discord pour interagir avec le serveur
- Notifications automatiques pour les événements importants

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
select *from users ;

select * from classement ;

select * from items ;
scp root@212.227.47.132:/root/bot/bot_conan/discord.db C:\Users\PAGOA\Documents\GitHub\Bot_Conan\


$!w49rG!!F


## Structure du Projet

```
Bot_Conan/
├── bot.py                   # Point d'entrée principal
├── config/
│   ├── settings.py          # Configuration
│   └── logging_config.py    # Configuration des logs
├── core/
│   ├── bot_core.py          # Classe principale du bot
│   └── commands.py          # Gestion des commandes Discord
├── features/
│   ├── build_tracker.py     # Suivi des constructions
│   ├── kill_tracker.py      # Suivi des kills
│   ├── player_tracker.py    # Suivi des joueurs
│   └── clan_tracker.py      # Suivi des clans
├── database/
│   ├── _ini_.py                # Ce fichier permet à Python de reconnaître ce répertoire comme un package 
│   ├── create_items_table.py   # Ce fichier permet à Python de reconnaître ce répertoire comme un package 
│   ├── database_build.py       # Gestion de la base de données
│   ├── database_classement.py  # Gestion de la base de données
│   ├── database_sync.py
│   └── init_database.py
├── utils/
│   ├── rcon_client.py       # Client RCON
│   ├── ftp_handler.py       # Gestion FTP
│   └── helpers.py           # Fonctions utilitaires
└── requirements.txt
```

## Commandes Discord

- `!aide` : Affiche l'aide pour les commandes disponibles
- `!stats` : Affiche les statistiques de kills
- `!builds` : Affiche les constructions en cours
- `!players` : Affiche la liste des joueurs connectés
- `!clans` : Affiche les statistiques des clans

## Fonctionnalités Automatiques

- Mise à jour automatique du nom du canal avec le nombre de joueurs connectés
- Notifications des nouveaux kills
- Notifications des constructions terminées
- Suivi de l'activité des joueurs et des clans
- Sauvegarde automatique des statistiques

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


 # Liste des template_id pour le starter pack
            starter_items = [
                51020, 51312, 53002, 52001, 52002, 52003, 52004, 52005, 80852, 92226, 2708
            ]