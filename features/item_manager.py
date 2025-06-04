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

    def get_player_steamid(self, discord_id):
        """Récupère le steam_id du joueur à partir de son Discord ID (si synchronisé)"""
        try:
            conn = sqlite3.connect('discord.db')
            cursor = conn.cursor()
            cursor.execute("SELECT steam_id FROM users WHERE discord_id = ?", (discord_id,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                logger.warning(f"Aucun utilisateur trouvé pour discord_id {discord_id}")
                return None
            return row[0]
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du steam_id: {e}")
            return None

    def get_conid_from_steamid(self, steam_id):
        """Récupère le conid (index temporaire) du joueur à partir de son steam_id via ListPlayers"""
        try:
            resp = self.rcon_client.execute("ListPlayers")
            if not resp or not steam_id:
                return None
            lines = resp.splitlines()
            if lines and ("Idx" in lines[0] or "Char name" in lines[0] or "Player name" in lines[0]):
                lines = lines[1:]
            for line in lines:
                if steam_id in line:
                    parts = line.split("|")
                    if len(parts) >= 2:
                        conid = parts[0].strip()
                        return conid
            return None
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du conid: {e}")
            return None

    async def give_item_to_player(self, discord_id, item_id, count=1):
        """Donne un item spécifique à un joueur via son Discord ID (utilise conid comme identifiant RCON)"""
        if not self.can_modify_inventory():
            logger.warning("Système verrouillé, impossible de donner l'item maintenant")
            return False, "Système verrouillé, réessaie dans quelques secondes."
        
        if not _global_lock.acquire(blocking=False):
            logger.warning(f"Une autre opération est en cours")
            return False, "Une autre opération est en cours, réessaie dans quelques secondes."
        
        try:
            steam_id = self.get_player_steamid(discord_id)
            if not steam_id:
                return False, "Tu n'es pas enregistré. Utilise !register d'abord."
            conid = self.get_conid_from_steamid(steam_id)
            if not conid:
                return False, "Tu dois être connecté en jeu pour recevoir l'item."
            # Exécuter la commande RCON avec le conid
            command = f"con {conid} spawnitem {item_id} {count}"
            response = self.rcon_client.execute(command)
            if response and "Unknown command" not in response:
                logger.info(f"Item {item_id} (x{count}) ajouté avec succès pour conid {conid}")
                return True, None
            else:
                logger.error(f"Échec de l'ajout de l'item {item_id} pour conid {conid}. Réponse: {response}")
                return False, f"Erreur lors du give: {response}"
        except Exception as e:
            logger.error(f"Erreur lors de l'ajout de l'item {item_id}: {e}")
            return False, f"Erreur interne: {e}"
        finally:
            _global_lock.release()

    def is_player_online(self, steam_id):
        """Vérifie si le joueur avec ce steam_id est connecté au serveur Conan"""
        try:
            resp = self.rcon_client.execute("ListPlayers")
            if not resp or not steam_id:
                return False
            lines = resp.splitlines()
            for line in lines:
                if steam_id in line:
                    return True
            return False
        except Exception as e:
            logger.error(f"Erreur lors de la vérification de la présence en ligne: {e}")
            return False 