import discord
import asyncio
from database.database_build import DatabaseBuildManager

class BuildLimitTracker:
    def __init__(self, bot, channel_id, ftp_handler):
        self.bot = bot
        self.channel_id = channel_id
        self.ftp_handler = ftp_handler
        self.is_running = False
        self.update_task = None
        self.LIMITE_CONSTRUCTION = 12000

    async def start(self):
        """Démarre le suivi des constructions"""
        if self.is_running:
            return
        
        self.is_running = True
        self.update_task = self.bot.loop.create_task(self._update_loop())

    async def stop(self):
        """Arrête le suivi des constructions"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self.update_task:
            self.update_task.cancel()
            try:
                await self.update_task
            except asyncio.CancelledError:
                pass

    async def _update_loop(self):
        """Boucle de mise à jour des constructions"""
        while self.is_running:
            try:
                await self._check_buildings()
                await asyncio.sleep(3600)  # Mise à jour toutes les heures
            except Exception as e:
                print(f"Erreur dans la boucle de mise à jour : {e}")
                await asyncio.sleep(60)  # Attendre avant de réessayer

    async def _check_buildings(self):
        """Vérifie les constructions et envoie un rapport"""
        try:
            # Récupérer les données depuis le FTP
            database = DatabaseBuildManager()
            constructions = database.get_constructions_by_player(self.ftp_handler)
            
            if not constructions:
                message = "Aucune construction trouvée."
                channel = self.bot.get_channel(self.channel_id)
                await channel.send(message)
                return

            # Regrouper les constructions par clan
            clans = {}
            for player in constructions:
                clan = player['clan'] if player['clan'] else "Sans clan"
                if clan not in clans:
                    clans[clan] = {'total': 0, 'players': 0}
                clans[clan]['total'] += player['instances']
                clans[clan]['players'] += 1
            
            # Calculer la moyenne par joueur pour chaque clan
            clans_list = []
            for clan_name, data in clans.items():
                if data['players'] > 0:  # Éviter la division par zéro
                    average = data['total'] / data['players']
                    clans_list.append({
                        'name': clan_name,
                        'total': data['total'],
                        'players': data['players'],
                        'average': round(average)  # Arrondir à l'entier
                    })
            
            # Trier les clans par moyenne d'instances
            clans_list.sort(key=lambda x: x['average'], reverse=True)
            
            # Construire le message
            message = ""
            
            # Ajouter le titre et la ligne de séparation
            message += f"Nombre de pièces de construction par clan (Limite: {self.LIMITE_CONSTRUCTION} pièces) :\n"
            message += "----------------------------------------\n\n"
            
            # Ajouter uniquement les clans qui dépassent la limite
            has_exceeded_limit = False
            for clan in clans_list:
                if clan['average'] > 0 and clan['average'] > self.LIMITE_CONSTRUCTION:
                    has_exceeded_limit = True
                    excess = clan['average'] - self.LIMITE_CONSTRUCTION
                    message += f"❌ **Clan ({clan['name']})** : {clan['average']} pièces (+{excess} au-dessus de la limite)\n\n"

            # Si aucun clan ne dépasse la limite, ajouter le message de félicitations
            if not has_exceeded_limit:
                message += f"✅ **Bravo ! Tous les clans respectent la limite de construction ({self.LIMITE_CONSTRUCTION} pièces maximum) !**"

            # Envoyer le message dans le salon de rapport
            report_channel = self.bot.get_channel(self.channel_id)
            if report_channel:
                try:
                    # Supprimer tous les messages existants
                    await report_channel.purge(limit=10)
                    
                    # Attendre un court instant pour s'assurer que les messages sont supprimés
                    await asyncio.sleep(1)
                    
                    # Envoyer le nouveau message
                    await report_channel.send(message)
                except Exception as e:
                    print(f"Erreur lors de l'envoi des messages : {e}")

        except Exception as e:
            error_message = f"❌ Erreur : {e}"
            channel = self.bot.get_channel(self.channel_id)
            if channel:
                await channel.send(error_message)
            print(f"Erreur dans la vérification des constructions : {e}")
