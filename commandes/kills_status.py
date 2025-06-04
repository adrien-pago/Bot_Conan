from discord.ext import commands

class KillsStatus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='kills_status')
    async def kills_status_command(self, ctx):
        """Commande pour vérifier l'état du KillTracker et forcer son démarrage si nécessaire"""
        if not ctx.author.guild_permissions.administrator:
            await ctx.send("❌ Cette commande est réservée aux administrateurs.")
            return
        try:
            if not hasattr(self.bot, 'kill_tracker') or self.bot.kill_tracker is None:
                await ctx.send("❌ KillTracker n'est pas initialisé.")
                return
            is_running = self.bot.kill_tracker.update_kills_task.is_running()
            if is_running:
                status_text = "✅ En cours d'exécution"
            else:
                status_text = "❌ Arrêté"
            await ctx.send(f"État actuel du KillTracker: {status_text}")
            channel_id = self.bot.kill_tracker.channel_id
            channel = self.bot.get_channel(channel_id)
            if channel:
                await ctx.send(f"Canal configuré: {channel.name} (ID: {channel_id})")
            else:
                await ctx.send(f"❌ Canal introuvable (ID: {channel_id})")
            if not is_running:
                await ctx.send("⏳ Tentative de démarrage du KillTracker...")
                try:
                    try:
                        self.bot.kill_tracker.update_kills_task.stop()
                    except Exception:
                        pass
                    await self.bot.kill_tracker.start()
                    if self.bot.kill_tracker.update_kills_task.is_running():
                        await ctx.send("✅ KillTracker démarré avec succès!")
                    else:
                        await ctx.send("❌ Échec du démarrage du KillTracker.")
                except Exception as e:
                    await ctx.send(f"❌ Erreur lors du démarrage du KillTracker: {str(e)}")
            await ctx.send("⏳ Exécution manuelle de la mise à jour...")
            try:
                await self.bot.kill_tracker.display_kills(ctx)
                await ctx.send("✅ Mise à jour effectuée.")
            except Exception as e:
                await ctx.send(f"❌ Erreur lors de la mise à jour manuelle: {str(e)}")
        except Exception as e:
            await ctx.send(f"❌ Erreur: {str(e)}")
            print(f"Erreur kills_status_command: {e}")

async def setup(bot):
    await bot.add_cog(KillsStatus(bot)) 