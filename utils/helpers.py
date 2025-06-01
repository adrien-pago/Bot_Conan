import logging
import asyncio
from datetime import datetime, timedelta
from config.logging_config import setup_logging

logger = setup_logging()

def format_time_delta(delta):
    """Formate un timedelta en une chaîne lisible"""
    days = delta.days
    hours = delta.seconds // 3600
    minutes = (delta.seconds % 3600) // 60
    
    if days > 0:
        return f"{days}j {hours}h {minutes}m"
    elif hours > 0:
        return f"{hours}h {minutes}m"
    else:
        return f"{minutes}m"
        
def format_player_name(name):
    """Formate le nom d'un joueur pour l'affichage"""
    return name.strip().title()
    
def format_clan_name(name):
    """Formate le nom d'un clan pour l'affichage"""
    if not name:
        return "Sans clan"
    return name.strip().upper()
    
def calculate_kd_ratio(kills, deaths):
    """Calcule le ratio K/D"""
    if deaths == 0:
        return kills
    return round(kills / deaths, 2)
    
def is_valid_player_name(name):
    """Vérifie si un nom de joueur est valide"""
    if not name or not isinstance(name, str):
        return False
    name = name.strip()
    return len(name) >= 3 and len(name) <= 32
    
def is_valid_clan_name(name):
    """Vérifie si un nom de clan est valide"""
    if not name:
        return True  # Clan vide est valide
    name = name.strip()
    return len(name) >= 2 and len(name) <= 32
    
def format_timestamp(timestamp):
    """Formate un timestamp en une chaîne lisible"""
    if not timestamp:
        return "Jamais"
    return timestamp.strftime("%d/%m/%Y %H:%M")
    
def calculate_level_progress(current_xp, next_level_xp):
    """Calcule la progression vers le niveau suivant"""
    if next_level_xp <= current_xp:
        return 100
    return int((current_xp / next_level_xp) * 100)
    
def format_build_progress(progress):
    """Formate la progression d'une construction"""
    return f"{progress}%"
    
def format_player_stats(stats):
    """Formate les statistiques d'un joueur pour l'affichage"""
    return {
        'name': format_player_name(stats['char_name']),
        'level': stats['level'],
        'clan': format_clan_name(stats.get('guild')),
        'kills': stats.get('kills', 0),
        'deaths': stats.get('deaths', 0),
        'kd_ratio': calculate_kd_ratio(stats.get('kills', 0), stats.get('deaths', 0)),
        'last_seen': format_timestamp(stats.get('lastTimeOnline')),
        'is_alive': stats.get('isAlive', True)
    }
    
def format_clan_stats(stats):
    """Formate les statistiques d'un clan pour l'affichage"""
    return {
        'name': format_clan_name(stats['name']),
        'kills': stats['total_kills'],
        'deaths': stats['total_deaths'],
        'kd_ratio': calculate_kd_ratio(stats['total_kills'], stats['total_deaths']),
        'members': stats['member_count'],
        'last_activity': format_timestamp(stats.get('last_activity'))
    }
    
def format_build_info(build):
    """Formate les informations d'une construction pour l'affichage"""
    return {
        'name': build['name'],
        'progress': format_build_progress(build['progress']),
        'time_left': format_time_delta(build['end_time'] - datetime.now()),
        'is_completed': build['is_completed']
    }
    
def is_player_online(last_seen):
    """Vérifie si un joueur est en ligne"""
    if not last_seen:
        return False
    return (datetime.now() - last_seen) < timedelta(minutes=5)
    
def is_clan_active(last_activity):
    """Vérifie si un clan est actif"""
    if not last_activity:
        return False
    return (datetime.now() - last_activity) < timedelta(days=1)
    
def format_error_message(error):
    """Formate un message d'erreur pour l'affichage"""
    return f"❌ Une erreur est survenue : {str(error)}"
    
def format_success_message(message):
    """Formate un message de succès pour l'affichage"""
    return f"✅ {message}"
    
def format_warning_message(message):
    """Formate un message d'avertissement pour l'affichage"""
    return f"⚠️ {message}"
    
def format_info_message(message):
    """Formate un message d'information pour l'affichage"""
    return f"ℹ️ {message}" 