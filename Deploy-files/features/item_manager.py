import logging
import sqlite3
import threading
import time
import os
from config.logging_config import setup_logging
import asyncio
import valve.rcon

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

    async def _execute_rcon_command(self, command, max_attempts=5):
        """Exécute une commande RCON avec système de retry"""
        attempts = 0
        while attempts < max_attempts:
            try:
                with valve.rcon.RCON((self.rcon_client.host, self.rcon_client.port), self.rcon_client.password) as rcon:
                    response = rcon.execute(command)
                    logger.info(f"Réponse RCON: {response.text}")
                    return True, response.text
            except valve.rcon.RCONAuthenticationError:
                logger.error("Erreur d'authentification RCON")
                attempts += 1
                await asyncio.sleep(1)
            except ConnectionResetError:
                logger.error("Erreur de connexion au serveur (karma)")
                attempts += 5  # On attend plus longtemps en cas de karma
                await asyncio.sleep(5)
            except Exception as e:
                logger.error(f"Erreur RCON: {e}")
                attempts += 1
                await asyncio.sleep(1)
        return False, None

    async def give_starter_pack_by_steam_id(self, steam_id):
        """Donne le pack de départ à un joueur via RCON en utilisant son Steam ID"""
        if not self.can_modify_inventory():
            logger.warning("Système verrouillé, impossible de donner le starter pack maintenant")
            return False

        if not _global_lock.acquire(blocking=False):
            logger.warning(f"Une autre opération est en cours pour le joueur avec Steam ID {steam_id}")
            _global_lock.release()
            return False

        try:
            logger.info(f"Début de l'ajout du pack de départ pour le joueur avec Steam ID {steam_id}")
            
            # Récupérer les informations des joueurs en ligne
            resp = self.rcon_client.execute("ListPlayers")
            logger.info(f"Réponse brute de ListPlayers: {resp}")
            
            # Extraire les informations des joueurs
            lines = resp.splitlines()
            if lines and ("Idx" in lines[0] or "Char name" in lines[0] or "Player name" in lines[0]):
                lines = lines[1:]
            
            # Chercher le joueur par son Steam ID
            target_player_name = None
            player_conid = None
            
            for line in lines:
                if steam_id in line:
                    parts = line.split("|")
                    if len(parts) >= 2:
                        target_player_name = parts[1].strip()
                        player_conid = parts[0].strip()  # Récupérer le conid (index du joueur)
                        break
            
            if not target_player_name or not player_conid:
                logger.error(f"Joueur avec Steam ID {steam_id} non trouvé en ligne ou ID manquant")
                return False

            # Mettre à jour le conid dans la base de données
            try:
                conn = sqlite3.connect('shop.db')
                cursor = conn.cursor()
                cursor.execute("UPDATE users SET conid = ? WHERE steam_id = ?", (player_conid, steam_id))
                conn.commit()
                conn.close()
                logger.info(f"Conid {player_conid} mis à jour pour le joueur {target_player_name}")
            except Exception as e:
                logger.error(f"Erreur lors de la mise à jour du conid: {e}")

            success_count = 0
            error_count = 0
            
            for item_id in self.starter_items:
                try:
                    # Utiliser la commande RCON avec le conid du joueur
                    command = f"con {player_conid} spawnitem {item_id} 1"
                    logger.info(f"Exécution de la commande: {command}")
                    
                    success, response = await self._execute_rcon_command(command)
                    if success and "Couldn't find a valid player" not in response:
                        logger.info(f"Item {item_id} ajouté avec succès pour '{target_player_name}'")
                        success_count += 1
                    else:
                        logger.error(f"Échec de l'ajout de l'item {item_id} pour '{target_player_name}'")
                        error_count += 1
                    
                    # Attendre un peu entre chaque commande
                    await asyncio.sleep(0.2)
                    
                except Exception as e:
                    logger.error(f"Erreur lors de l'ajout de l'item {item_id}: {e}")
                    error_count += 1
            
            logger.info(f"Starter pack pour '{target_player_name}' (Steam ID: {steam_id}): {success_count} items ajoutés, {error_count} échecs")
            return success_count > 0

        except Exception as e:
            logger.error(f"Erreur lors de l'ajout du pack de départ: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
        finally:
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