# 🏛️ Bot Conan Exiles Discord

Un bot Discord avancé pour la gestion et la surveillance d'un serveur Conan Exiles. Ce bot offre une suite complète d'outils pour les administrateurs et les joueurs, incluant le suivi des activités, la gestion des items, un système de boutique, et bien plus encore.

## ✨ Fonctionnalités Principales

### 🎮 Gestion des Joueurs
- **Suivi en temps réel** des joueurs connectés/déconnectés
- **Synchronisation automatique** des données joueurs avec la base de données du serveur
- **Mise à jour automatique** du nom du canal avec le nombre de joueurs connectés
- **Système d'informations** des joueurs via messages privés

### 🏹 Système de Combat et Classement
- **Suivi des kills et morts** en temps réel
- **Classement des joueurs** par nombre de kills
- **Statistiques détaillées** des combats
- **Notifications automatiques** des événements PvP

### 🏗️ Gestion des Constructions
- **Limite de construction** configurable (défaut: 12,000 pièces)
- **Surveillance automatique** des constructions en cours
- **Notifications** quand les limites sont atteintes
- **Suivi des bâtiments** par joueur/clan

### 🛒 Système de Boutique
- **Boutique in-game** avec interface Discord élégante
- **Catégories d'items** : Armes, Outils, Ressources, Stockage, Pets, Potions
- **Système de coins** pour les achats
- **Gestion des inventaires** et starter packs
- **Interface stylée** avec embeds Discord colorés

### 🗳️ Système de Votes
- **Votes pour serveur privé** ou public
- **Intégration avec les sites de classement** de serveurs
- **Notifications automatiques** des résultats de votes

### 🔧 Administration RCON
- **Commandes RCON** directement depuis Discord
- **Démarrage/arrêt** du serveur à distance
- **Gestion des joueurs** (kick, ban, etc.)
- **Exécution de commandes** personnalisées

## 🚀 Installation

### Prérequis
- **Python 3.10 ou 3.11** (⚠️ **Pas compatible avec Python 3.12** à cause de `python-valve`)
- **Serveur Conan Exiles** avec accès RCON et FTP
- **Bot Discord** avec les permissions appropriées

### 1. Cloner le projet
```bash
git clone https://github.com/votre-username/Bot_Conan.git
cd Bot_Conan
```

### 2. Installer les dépendances
```bash
pip install -r requirements.txt
```

**Note importante** : Si vous utilisez Python 3.12, vous devrez downgrader vers Python 3.10 ou 3.11 car `python-valve` n'est pas encore compatible.

### 3. Configuration
Créez un fichier `.env` à la racine du projet :

```env
# Discord Configuration
DISCORD_TOKEN=votre_token_discord_ici
RENAME_CHANNEL_ID=1375223092892401737
BUILD_CHANNEL_ID=1375234869071708260
KILLS_CHANNEL_ID=1375234869071708260
TOP_SERVER_CHANNEL_ID=1368550677030109225
SERVER_PRIVE_CHANNEL_ID=1369099859574915192
SHOP_CHANNEL_ID=1379725647579975730
COMMANDE_CHANNEL_ID=1375046216097988629

# Serveur de Jeu
GAME_SERVER_HOST=votre_ip_serveur
RCON_PORT=25575
RCON_PASSWORD=votre_mot_de_passe_rcon

# FTP Configuration
FTP_HOST=votre_ip_ftp
FTP_USER=votre_utilisateur_ftp
FTP_PASS=votre_mot_de_passe_ftp
FTP_DB_PATH=chemin/vers/game.db
FTP_LOG_PATH=Saved/Logs/ConanSandbox.log
```

### 4. Lancer le bot
```bash
python bot.py
```

## 🐧 Déploiement sur VPS Linux

### 1. Préparation locale
Utilisez le script PowerShell pour préparer les fichiers de déploiement :
```powershell
.\deploy.ps1
```

### 2. Transfert vers le VPS
```bash
scp -r Deploy-files/* root@votre_ip:/root/bot/bot_conan/
```

### 3. Installation sur le VPS
```bash
# Mise à jour du système
apt update && apt upgrade -y

# Installation de Python et pip
apt install -y python3 python3-pip

# Installation des dépendances
cd /root/bot/bot_conan
pip3 install -r requirements.txt

# Configuration du service systemd
cp bot_conan.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable bot_conan
systemctl start bot_conan
```

### 4. Gestion du service
```bash
# Voir le statut
systemctl status bot_conan

# Redémarrer
systemctl restart bot_conan

# Arrêter
systemctl stop bot_conan

# Voir les logs en temps réel
journalctl -u bot_conan -f
```

## 🎯 Commandes Discord

### Commandes Générales
- `!info` - Affiche les informations du joueur (en MP uniquement)
- `!register` - Enregistre un nouveau joueur
- `!solde` - Affiche le solde de coins du joueur

### Commandes de Boutique
- `!shop` - Affiche la boutique avec tous les items disponibles
- `!buy <id_item> [quantité]` - Achète un item de la boutique

### Commandes d'Administration
- `!start` - Démarre le serveur Conan Exiles
- `!stop` - Arrête le serveur Conan Exiles
- `!rcon <commande>` - Exécute une commande RCON

### Commandes de Statistiques
- `!kills_status` - Affiche les statistiques de kills
- `!build` - Affiche les informations de construction

### Commandes de Gestion
- `!starterpack` - Gère les starter packs des joueurs

## 🏗️ Architecture du Projet

```
Bot_Conan/
├── 📁 bot.py                    # Point d'entrée principal
├── 📁 requirements.txt          # Dépendances Python
├── 📁 .env                      # Variables d'environnement
├── 📁 deploy.ps1                # Script de déploiement
├── 📁 bot_conan.service         # Service systemd
│
├── 📂 commandes/                # Commandes Discord (Cogs)
│   ├── build.py                 # Commandes de construction
│   ├── buy.py                   # Système d'achat
│   ├── info.py                  # Informations joueur
│   ├── kills_status.py          # Statistiques de combat
│   ├── rcon.py                  # Commandes RCON
│   ├── register.py              # Enregistrement joueurs
│   ├── shop.py                  # Boutique Discord
│   ├── solde.py                 # Gestion des coins
│   ├── start.py                 # Démarrage serveur
│   ├── starterpack.py           # Gestion starter packs
│   └── stop.py                  # Arrêt serveur
│
├── 📂 features/                 # Fonctionnalités principales
│   ├── build_limit.py           # Limitation constructions
│   ├── classement_player.py     # Système de classement
│   ├── item_manager.py          # Gestion des items
│   ├── player_sync.py           # Synchronisation joueurs
│   ├── player_tracker.py        # Suivi des joueurs
│   └── vote_tracker.py          # Système de votes
│
├── 📂 database/                 # Gestion base de données
│   ├── init_database.py         # Initialisation BDD
│   ├── database_sync.py         # Synchronisation données
│   ├── database_classement.py   # Gestion classements
│   ├── database_build.py        # Gestion constructions
│   └── create_items_table.py    # Création tables items
│
├── 📂 utils/                    # Utilitaires
│   ├── rcon_client.py           # Client RCON
│   ├── ftp_handler.py           # Gestionnaire FTP
│   └── helpers.py               # Fonctions utilitaires
│
├── 📂 config/                   # Configuration
│   ├── settings.py              # Paramètres généraux
│   └── logging_config.py        # Configuration logs
│
└── 📂 core/                     # Composants principaux
    ├── bot_core.py              # Classe principale du bot
    └── commands.py              # Gestion des commandes
```

## 🔧 Configuration Avancée

### Variables d'Environnement Détaillées

| Variable | Description | Valeur par défaut |
|----------|-------------|-------------------|
| `DISCORD_TOKEN` | Token du bot Discord | **Requis** |
| `RENAME_CHANNEL_ID` | Canal de suivi des joueurs | `1375223092892401737` |
| `BUILD_CHANNEL_ID` | Canal des constructions | `1375234869071708260` |
| `KILLS_CHANNEL_ID` | Canal des kills | `1375234869071708260` |
| `SHOP_CHANNEL_ID` | Canal de la boutique | `1379725647579975730` |
| `GAME_SERVER_HOST` | IP du serveur de jeu | **Requis** |
| `RCON_PORT` | Port RCON | `25575` |
| `RCON_PASSWORD` | Mot de passe RCON | **Requis** |
| `FTP_HOST` | Serveur FTP | **Requis** |
| `FTP_USER` | Utilisateur FTP | **Requis** |
| `FTP_PASS` | Mot de passe FTP | **Requis** |

### Paramètres de Jeu

- **Limite de construction** : 12,000 pièces par défaut
- **Joueurs maximum** : 40
- **Intervalles de mise à jour** :
  - Canal joueurs : 8 minutes
  - Vérification constructions : 5 minutes
  - Mise à jour kills : 1 minute

### Heures de Raid
- **Jours** : Samedi et Dimanche (5, 6)
- **Heures** : 20h00 - 23h00

## 📊 Base de Données

Le bot utilise **SQLite** pour stocker les données :

### Tables Principales
- `players` - Informations des joueurs
- `kills` - Historique des kills
- `builds` - Données de construction
- `items` - Catalogue de la boutique
- `transactions` - Historique des achats
- `votes` - Système de votes

### Synchronisation
- **Automatique** avec la base de données du serveur Conan Exiles
- **Temps réel** pour les événements critiques
- **Sauvegarde** régulière des statistiques

## 🔍 Fonctionnalités Automatiques

### Surveillance en Temps Réel
- ✅ Connexions/déconnexions des joueurs
- ✅ Nouveaux kills et morts
- ✅ Constructions terminées
- ✅ Dépassement des limites de construction
- ✅ Votes sur les sites de classement

### Notifications Discord
- 🔔 Événements PvP importants
- 🔔 Alertes de construction
- 🔔 Changements de statut du serveur
- 🔔 Résultats de votes

### Maintenance Automatique
- 🔄 Nettoyage des anciens logs
- 🔄 Optimisation de la base de données
- 🔄 Mise à jour des statistiques
- 🔄 Synchronisation des données

## ⚠️ Problèmes Connus et Solutions

### Problème de Compatibilité Python 3.12
**Erreur** : `ModuleNotFoundError: No module named 'valve.rcon'`

**Solution** : Le package `python-valve` n'est pas compatible avec Python 3.12. Utilisez Python 3.10 ou 3.11.

```bash
# Vérifier votre version de Python
python --version

# Si vous avez Python 3.12, installez Python 3.10 ou 3.11
# Puis créez un environnement virtuel avec la bonne version
```

### Problèmes de Connexion RCON
- Vérifiez que le port RCON est ouvert sur votre serveur
- Confirmez que le mot de passe RCON est correct
- Assurez-vous que le serveur Conan Exiles est démarré

### Problèmes FTP
- Vérifiez les permissions d'accès aux fichiers
- Confirmez que le chemin vers la base de données est correct
- Testez la connexion FTP manuellement

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :

1. 🍴 **Fork** le projet
2. 🌟 **Créer** une branche pour votre fonctionnalité
3. 📝 **Commiter** vos changements
4. 🚀 **Push** vers la branche
5. 🔄 **Ouvrir** une Pull Request

## 📜 Licence

Ce projet est sous licence MIT. Voir le fichier `LICENSE` pour plus de détails.

## 🆘 Support

Pour obtenir de l'aide :
- 📧 Ouvrez une **issue** sur GitHub
- 💬 Rejoignez notre **serveur Discord**
- 📖 Consultez la **documentation** complète

---

**Développé avec ❤️ pour la communauté Conan Exiles**
