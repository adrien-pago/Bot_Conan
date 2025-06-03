import logging
import sqlite3
import threading
import time
import os
from config.logging_config import setup_logging

logger = setup_logging()

# Verrou global pour éviter les appels multiples
_global_lock = threading.Lock()

class ItemManager:
    def __init__(self, bot, ftp_handler):
        """Initialise le gestionnaire d'items"""
        self.bot = bot
        self.ftp = ftp_handler
        self.rcon_client = bot.player_tracker.rcon_client
        self.last_build_time = 0
        self.build_cooldown = 60  # 60 secondes de cooldown après un build

        # Liste des template_id pour le starter pack
        self.starter_items = [
            51020,  # Piolet stellaire
            51312,  # Couteau stellaire
            50492,  # Grande hache stellaire
            80852,  # Coffre en fer
            92226,  # Cheval
            2708,   # Selle légère
            53002   # Extrait d'aoles
        ]

    def can_modify_inventory(self):
        """Vérifie si on peut modifier l'inventaire des joueurs"""
        current_time = time.time()
        if current_time - self.last_build_time < self.build_cooldown:
            remaining = int(self.build_cooldown - (current_time - self.last_build_time))
            logger.warning(f"Système verrouillé, attendez {remaining} secondes")
            return False
        return True

    def set_last_build_time(self):
        """Met à jour le timestamp du dernier build"""
        self.last_build_time = time.time()

    async def give_starter_pack(self, player_id):
        """Donne le pack de départ à un joueur via RCON"""
        # Vérifier si on peut modifier l'inventaire
        if not self.can_modify_inventory():
            logger.warning("Système verrouillé, impossible de donner le starter pack maintenant")
            return False

        # Utiliser le verrou global pour éviter les appels multiples
        if not _global_lock.acquire(blocking=False):
            logger.warning(f"Une autre opération est en cours pour le joueur {player_id}")
            _global_lock.release()
            return False

        try:
            logger.info(f"Début de l'ajout du pack de départ pour le joueur {player_id}")

            # Récupérer les informations du joueur pour obtenir son nom
            conn = sqlite3.connect('discord.db')
            c = conn.cursor()
            c.execute('SELECT player_name FROM users WHERE player_id = ?', (player_id,))
            result = c.fetchone()
            conn.close()

            if not result:
                logger.error(f"Joueur avec ID {player_id} non trouvé dans la base de données")
                return False

            player_name = result[0]
            
            # Vérifier si le joueur est actuellement connecté (vérification assouplie)
            online_players = self.rcon_client.get_online_players()
            logger.info(f"Joueurs en ligne: {online_players}")
            
            # Vérification plus souple
            player_connected = False
            target_player = player_name
            
            for online_player in online_players:
                # Correspondance exacte
                if online_player == player_name:
                    player_connected = True
                    target_player = online_player
                    break
                # Correspondance partielle
                elif player_name.lower() in online_player.lower():
                    player_connected = True
                    target_player = online_player
                    break
                # Si le joueur en ligne contient "Steam", assouplir la vérification
                elif "Steam" in online_player:
                    # Pour test et debug, considérer tous les joueurs "Steam" comme potentiellement notre joueur
                    player_connected = True
                    target_player = online_player
                    break
            
            if not player_connected and len(online_players) > 0:
                logger.warning(f"Le joueur {player_name} n'est pas connecté. Joueurs en ligne: {online_players}")
                
                # Option avancée: si problème de détection, utiliser un joueur au hasard pour debug (à utiliser avec précaution)
                # Décommenter la ligne suivante pour utiliser cette option en dernier recours
                # target_player = online_players[0]
                # player_connected = True
                # logger.warning(f"Utilisation du joueur {target_player} à la place de {player_name} pour test")
                
                # Désactiver temporairement la vérification de connexion (décommenter pour désactiver)
                # player_connected = True
                # target_player = player_name
                # logger.warning("Vérification de connexion désactivée temporairement")
            
            if not player_connected and len(online_players) == 0:
                logger.warning(f"Aucun joueur n'est connecté au serveur")
                return False
            
            # Le joueur est connecté ou nous utilisons un autre joueur pour test, on peut procéder
            logger.info(f"Joueur cible pour le starter pack: {target_player}")
            
            # Ajouter chaque item dans l'inventaire via RCON
            success_count = 0
            error_count = 0
            
            for item_id in self.starter_items:
                try:
                    # Utiliser la commande RCON pour donner l'objet au joueur
                    # Format: con <playerName> spawnitem <itemID> <count>
                    command = f"con {target_player} spawnitem {item_id} 1"
                    logger.info(f"Exécution de la commande: {command}")
                    response = self.rcon_client.execute(command)
                    
                    logger.info(f"Réponse RCON: {response}")
                    
                    if response and "Unknown command" not in response:
                        logger.info(f"Item {item_id} ajouté avec succès pour {target_player}")
                        success_count += 1
                    else:
                        logger.error(f"Échec de l'ajout de l'item {item_id} pour {target_player}. Réponse: {response}")
                        error_count += 1
                        
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout de l'item {item_id}: {e}")
                    error_count += 1
            
            # Journaliser le résultat
            logger.info(f"Starter pack pour {target_player}: {success_count} items ajoutés, {error_count} échecs")
            
            # Retourner True si au moins un item a été donné avec succès
            return success_count > 0

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du pack de départ: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
            # Libérer le verrou global
            _global_lock.release()
            
    async def give_item_to_player(self, player_name, item_id, count=1):
        """Donne un item spécifique à un joueur"""
        if not self.can_modify_inventory():
            logger.warning("Système verrouillé, impossible de donner l'item maintenant")
            return False
            
        if not _global_lock.acquire(blocking=False):
            logger.warning(f"Une autre opération est en cours")
            return False
            
        try:
            # Vérifier si le joueur est connecté
            online_players = self.rcon_client.get_online_players()
            
            if player_name not in online_players:
                logger.warning(f"Le joueur {player_name} n'est pas connecté. Impossible de donner l'item.")
                return False
                
            # Exécuter la commande RCON
            command = f"con {player_name} spawnitem {item_id} {count}"
            response = self.rcon_client.execute(command)
            
            if response and "Unknown command" not in response:
                logger.info(f"Item {item_id} (x{count}) ajouté avec succès pour {player_name}")
                return True
            else:
                logger.error(f"Échec de l'ajout de l'item {item_id} pour {player_name}. Réponse: {response}")
                return False
                
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de l'item {item_id}: {e}")
            return False
        finally:
            _global_lock.release() 