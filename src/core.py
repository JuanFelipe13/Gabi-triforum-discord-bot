import discord
from discord.ext import commands
import os
import json
from dotenv import load_dotenv
import logging
from pathlib import Path
import sys

from .commands import setup_commands

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Cargar variables de entorno desde .env
load_dotenv()

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

class MusicBot(commands.Bot):
    def __init__(self):
        # Cargar configuración
        config_path = resource_path('config.json')
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
            
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix=self.config.get('command_prefix', '!'),
            intents=intents
        )
        
        # Cargar token
        self.discord_token = os.getenv('DISCORD_TOKEN')
        if not self.discord_token:
            raise ValueError("No se encontró el token de Discord en las variables de entorno")
        
        # Configurar comandos
        setup_commands(self)
        
    async def on_ready(self):
        logger.info(f'Bot de música conectado como {self.user}')
        
    async def on_voice_state_update(self, member, before, after):
        """Desconectar el bot si se queda solo en el canal"""
        if before.channel is None or after.channel is not None:
            return

        voice_client = discord.utils.get(self.voice_clients, channel=before.channel)
        if voice_client:
            # Verificar si el bot está solo en el canal
            members = before.channel.members
            if len(members) == 1 and members[0] == self.user:
                await voice_client.disconnect()
                logger.info(f'Bot desconectado del canal {before.channel} por estar solo')
