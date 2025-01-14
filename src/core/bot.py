import discord
from discord.ext import commands
import os
from pathlib import Path
import json
import logging
from functools import lru_cache
from typing import Optional, Dict
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

CONFIG_FILE = Path('config.json')
DEFAULT_PREFIX = '!'
CACHE_SIZE = 128

class MusicBot(commands.Bot):
    def __init__(self):
        self._load_initial_config()
        
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix=self._get_prefix,
            case_insensitive=True,
            intents=intents
        )
        
        self.guild_configs: Dict[int, dict] = {}
        
    @lru_cache(maxsize=CACHE_SIZE)
    async def _get_prefix(self, bot, message):
        if not message.guild:
            return DEFAULT_PREFIX
        
        guild_id = message.guild.id
        if guild_id not in self.guild_configs:
            return self.config.get('command_prefix', DEFAULT_PREFIX)
            
        return self.guild_configs[guild_id].get('prefix', DEFAULT_PREFIX)

    def _load_initial_config(self):
        try:
            load_dotenv()
            
            self.config = json.loads(CONFIG_FILE.read_text()) if CONFIG_FILE.exists() else {}
            
            self.discord_token = (
                os.getenv('DISCORD_TOKEN') or 
                self.config.get('token') or 
                ''
            ).strip()
            
            if not self.discord_token:
                raise ValueError("Token de Discord no encontrado")
                
        except Exception as e:
            logger.error(f"Error cargando configuración: {str(e)}")
            raise

    async def setup_hook(self):
        await self._load_extensions()
        
    async def _load_extensions(self):
        try:
            await self.load_extension('src.commands')
        except Exception as e:
            logger.error(f"Error cargando extensiones: {e}")
            raise

    async def on_ready(self):
        await self._initialize_guild_configs()
        
    async def _initialize_guild_configs(self):
        for guild in self.guilds:
            self.guild_configs[guild.id] = {
                'prefix': self.config.get('command_prefix', DEFAULT_PREFIX)
            }
            
    async def on_voice_state_update(self, member, before, after):
        if member.bot:
            return
            
        if before.channel and not after.channel:
            voice_client = discord.utils.get(self.voice_clients, channel=before.channel)
            if not voice_client:
                return
                
            members = [m for m in before.channel.members if not m.bot]
            if not members:
                from ..core.state import players
                if voice_client.guild.id in players:
                    player = players[voice_client.guild.id]
                    player.queue.clear()
                    player.is_playing = False
                    player.current = None
                
                await voice_client.disconnect()
