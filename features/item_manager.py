import logging
import sqlite3
import threading
import time
import os
from config.logging_config import setup_logging
import asyncio

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

    async def give_starter_pack(self, player_name):
        """Donne le pack de départ à un joueur via RCON"""
        # Vérifier si on peut modifier l'inventaire
        if not self.can_modify_inventory():
            logger.warning("Système verrouillé, impossible de donner le starter pack maintenant")
            return False

        # Utiliser le verrou global pour éviter les appels multiples
        if not _global_lock.acquire(blocking=False):
            logger.warning(f"Une autre opération est en cours pour le joueur {player_name}")
            _global_lock.release()
            return False

        try:
            logger.info(f"Début de l'ajout du pack de départ pour le joueur '{player_name}'")
            
            # Vérifier si le joueur est connecté au serveur
            online_players = self.rcon_client.get_online_players()
            logger.info(f"Joueurs en ligne: {online_players}")
            
            player_found = False
            exact_player_name = player_name  # Nom exact tel qu'il apparaît dans la liste
            
            for online_player in online_players:
                if player_name.lower() == online_player.lower():
                    player_found = True
                    exact_player_name = online_player  # Utiliser le nom exact tel qu'il apparaît
                    logger.info(f"Joueur trouvé en ligne: '{online_player}'")
                    break
            
            if not player_found:
                logger.error(f"Joueur '{player_name}' non trouvé parmi les joueurs en ligne")
                return False
            
            # Ajouter chaque item dans l'inventaire via RCON en utilisant le nom du joueur
            success_count = 0
            error_count = 0
            
            for item_id in self.starter_items:
                try:
                    # Entourer le nom du joueur de guillemets s'il contient des espaces
                    player_name_for_command = f'"{exact_player_name}"' if ' ' in exact_player_name else exact_player_name
                    
                    # Utiliser la commande RCON pour donner l'objet au joueur
                    command = f"con {player_name_for_command} spawnitem {item_id} 1"
                    logger.info(f"Exécution de la commande: {command}")
                    
                    # Exécuter la commande et récupérer la réponse
                    response = self.rcon_client.execute(command)
                    logger.info(f"Réponse RCON pour item {item_id}: {response}")
                    
                    # Analyser la réponse pour déterminer si l'opération a réussi
                    if response and "Unknown command" not in response:
                        if "Error" in response or "error" in response or "failed" in response or "Failed" in response:
                            logger.error(f"Échec de l'ajout de l'item {item_id} pour '{exact_player_name}'. Réponse: {response}")
                            error_count += 1
                        else:
                            logger.info(f"Item {item_id} ajouté avec succès pour '{exact_player_name}'")
                            success_count += 1
                    else:
                        logger.error(f"Échec de l'ajout de l'item {item_id} pour '{exact_player_name}'. Réponse: {response}")
                        error_count += 1
                        
                    # Attendre un peu entre chaque commande pour éviter de surcharger le serveur
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout de l'item {item_id}: {e}")
                    error_count += 1
            
            # Journaliser le résultat
            logger.info(f"Starter pack pour '{exact_player_name}': {success_count} items ajoutés, {error_count} échecs")
            
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

    async def give_starter_pack_by_steam_id(self, steam_id):
        """Donne le pack de départ à un joueur via RCON en utilisant son Steam ID"""
        # Vérifier si on peut modifier l'inventaire
        if not self.can_modify_inventory():
            logger.warning("Système verrouillé, impossible de donner le starter pack maintenant")
            return False

        # Utiliser le verrou global pour éviter les appels multiples
        if not _global_lock.acquire(blocking=False):
            logger.warning(f"Une autre opération est en cours pour le joueur avec Steam ID {steam_id}")
            _global_lock.release()
            return False

        try:
            logger.info(f"Début de l'ajout du pack de départ pour le joueur avec Steam ID {steam_id}")
            
            # Récupérer les informations des joueurs en ligne avec ListPlayers
            resp = self.rcon_client.execute("ListPlayers")
            logger.info(f"Réponse brute de ListPlayers: {resp}")
            
            # Extraire les informations des joueurs
            lines = resp.splitlines()
            # Ignorer la ligne d'en-tête
            if lines and ("Idx" in lines[0] or "Char name" in lines[0] or "Player name" in lines[0]):
                lines = lines[1:]
            
            # Chercher le joueur par son Steam ID
            target_player_name = None
            platform_id_index = None
            player_id_index = None
            
            # Déterminer l'index de la colonne Platform ID
            if lines and len(lines) > 0 and "|" in lines[0]:
                headers = lines[0].split("|")
                for i, header in enumerate(headers):
                    if "Platform ID" in header:
                        platform_id_index = i
                    if "User ID" in header:  # Pour trouver l'ID utilisateur
                        player_id_index = i
            
            # Si on n'a pas trouvé l'index, utiliser des valeurs par défaut
            if platform_id_index is None:
                platform_id_index = 4  # Valeur par défaut selon le format observé
            if player_id_index is None:
                player_id_index = 3  # Valeur par défaut selon le format observé
            
            # Chercher le joueur par son Steam ID
            user_id = None
            for line in lines:
                if not line.strip() or "|" not in line:
                    continue
                
                parts = line.split("|")
                if len(parts) <= platform_id_index:
                    continue
                
                player_steam_id = parts[platform_id_index].strip()
                if player_steam_id == steam_id:
                    # Récupérer le nom du personnage (généralement dans la colonne 1)
                    if len(parts) >= 2:
                        target_player_name = parts[1].strip()
                        # Récupérer l'ID utilisateur si disponible
                        if player_id_index is not None and len(parts) > player_id_index:
                            user_id = parts[player_id_index].strip()
                        logger.info(f"Joueur trouvé: {target_player_name} avec Steam ID {steam_id} et User ID {user_id}")
                        break
            
            if not target_player_name:
                logger.error(f"Aucun joueur connecté avec Steam ID {steam_id}")
                return False
            
            # Ajouter chaque item dans l'inventaire via RCON en utilisant le nom du joueur ou l'ID
            success_count = 0
            error_count = 0
            
            for item_id in self.starter_items:
                try:
                    # Essayer plusieurs variantes de commandes
                    commands = []
                    
                    # Variante 1: con avec le nom du joueur entre guillemets
                    player_name_for_command = f'"{target_player_name}"' if ' ' in target_player_name else target_player_name
                    commands.append(f"con {player_name_for_command} spawnitem {item_id} 1")
                    
                    # Variante 2: ce SpawnItem avec l'ID utilisateur si disponible
                    if user_id:
                        commands.append(f"ce SpawnItem {user_id} {item_id} 1")
                    
                    # Variante 3: ce GiveItem avec le nom du joueur
                    commands.append(f"ce GiveItem {player_name_for_command} {item_id} 1")
                    
                    # Variante 4: spawnitems (commande alternative parfois disponible)
                    commands.append(f"spawnitems {player_name_for_command} {item_id} 1")
                    
                    # Essayer chaque commande jusqu'à ce qu'une fonctionne
                    command_success = False
                    for command in commands:
                        logger.info(f"Essai de la commande: {command}")
                        response = self.rcon_client.execute(command)
                        logger.info(f"Réponse RCON pour item {item_id}: {response}")
                        
                        # Vérifier si la commande a réussi
                        if response and "Unknown command" not in response and "Error" not in response and "error" not in response and "failed" not in response and "Failed" not in response:
                            logger.info(f"Item {item_id} ajouté avec succès pour '{target_player_name}' avec la commande: {command}")
                            success_count += 1
                            command_success = True
                            break
                    
                    if not command_success:
                        logger.error(f"Échec de l'ajout de l'item {item_id} pour '{target_player_name}' avec toutes les commandes essayées")
                        error_count += 1
                        
                    # Attendre un peu entre chaque commande pour éviter de surcharger le serveur
                    await asyncio.sleep(0.5)
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout de l'item {item_id}: {e}")
                    error_count += 1
            
            # Journaliser le résultat
            logger.info(f"Starter pack pour '{target_player_name}' (Steam ID: {steam_id}): {success_count} items ajoutés, {error_count} échecs")
            
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