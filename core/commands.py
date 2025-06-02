import discord
from discord.ext import commands
import logging
from config.settings import *
from config.logging_config import setup_logging

logger = setup_logging()

class BotCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
    @commands.command(name='aide')
    async def help_command(self, ctx):
        """Affiche l'aide pour les commandes disponibles"""
        embed = discord.Embed(
            title="Aide des commandes",
            description="Liste des commandes disponibles :",
            color=discord.Color.blue()
        )
        
        commands_list = [
            ("!aide", "Affiche ce message d'aide")
        ]
        
        for cmd, desc in commands_list:
            embed.add_field(name=cmd, value=desc, inline=False)
            
        await ctx.send(embed=embed)
        
    @commands.command(name='stats')
    async def stats_command(self, ctx):
        """Affiche les statistiques de kills"""
        try:
            stats = await self.bot.kill_tracker.get_stats()
            embed = discord.Embed(
                title="Statistiques des Kills",
                color=discord.Color.red()
            )
            
            for player, data in stats.items():
                embed.add_field(
                    name=player,
                    value=f"Kills: {data['kills']}\nMorts: {data['deaths']}",
                    inline=True
                )
                
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des stats: {e}")
            await ctx.send("❌ Une erreur est survenue lors de la récupération des statistiques.")
            
    @commands.command(name='builds')
    async def builds_command(self, ctx):
        """Affiche les constructions en cours"""
        try:
            builds = await self.bot.build_tracker.get_active_builds()
            embed = discord.Embed(
                title="Constructions en cours",
                color=discord.Color.green()
            )
            
            if not builds:
                embed.description = "Aucune construction en cours"
            else:
                for build in builds:
                    embed.add_field(
                        name=build['name'],
                        value=f"Progression: {build['progress']}%\nTemps restant: {build['time_left']}",
                        inline=True
                    )
                    
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des constructions: {e}")
            await ctx.send("❌ Une erreur est survenue lors de la récupération des constructions.")
            
    @commands.command(name='players')
    async def players_command(self, ctx):
        """Affiche la liste des joueurs connectés"""
        try:
            players = await self.bot.player_tracker.get_online_players()
            embed = discord.Embed(
                title="Joueurs connectés",
                color=discord.Color.gold()
            )
            
            if not players:
                embed.description = "Aucun joueur connecté"
            else:
                for player in players:
                    embed.add_field(
                        name=player['name'],
                        value=f"Niveau: {player['level']}\nClan: {player['clan']}",
                        inline=True
                    )
                    
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des joueurs: {e}")
            await ctx.send("❌ Une erreur est survenue lors de la récupération des joueurs.")
            
    @commands.command(name='clans')
    async def clans_command(self, ctx):
        """Affiche les statistiques des clans"""
        try:
            clans = await self.bot.clan_tracker.get_clan_stats()
            embed = discord.Embed(
                title="Statistiques des Clans",
                color=discord.Color.purple()
            )
            
            if not clans:
                embed.description = "Aucune statistique de clan disponible"
            else:
                for clan, stats in clans.items():
                    embed.add_field(
                        name=clan,
                        value=f"Kills: {stats['kills']}\nMorts: {stats['deaths']}\nMembres: {stats['members']}",
                        inline=True
                    )
                    
            await ctx.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Erreur lors de l'affichage des clans: {e}")
            await ctx.send("❌ Une erreur est survenue lors de la récupération des statistiques des clans.")
            
async def setup(bot):
    """Fonction d'initialisation du module de commandes"""
    await bot.add_cog(BotCommands(bot)) 