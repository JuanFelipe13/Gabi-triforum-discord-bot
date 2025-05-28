import discord
from discord.ext import commands
import os
from pathlib import Path
import json
import logging
from functools import lru_cache
from typing import Optional, Dict
from dotenv import load_dotenv

from .music_player import MusicPlayer

logger = logging.getLogger(__name__)

CONFIG_FILE = Path('config.json')
DEFAULT_PREFIX = '!'
CACHE_SIZE = 128

class MusicBot(commands.Bot):
    """The main Discord bot class extending commands.Bot."""
    def __init__(self):
        """Initializes bot intents, configuration, and prefix handling."""
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
        self.players: Dict[int, MusicPlayer] = {}
        self.audio_bitrate = 128  # Default bitrate in kbps
        self.audio_sampling_rate = 48000 # Default sampling rate in Hz
        self.audio_channels = 2 # Default audio channels (stereo)
        
    @lru_cache(maxsize=CACHE_SIZE)
    async def _get_prefix(self, bot, message):
        """Dynamically gets the command prefix for a given message/guild."""
        if not message.guild:
            return DEFAULT_PREFIX
        
        guild_id = message.guild.id
        if guild_id not in self.guild_configs:
            return self.config.get('command_prefix', DEFAULT_PREFIX)
            
        return self.guild_configs[guild_id].get('prefix', DEFAULT_PREFIX)

    def _load_initial_config(self):
        """Loads configuration from .env and config.json."""
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
        """Hook called by discord.py to perform async setup, loads extensions."""
        await self._load_extensions()
        
    async def _load_extensions(self):
        """Loads the command cogs."""
        try:
            await self.load_extension('src.commands')
        except Exception as e:
            logger.error(f"Error cargando extensiones: {e}")
            raise

    async def on_ready(self):
        """Event handler called when the bot is ready and connected."""
        await self._initialize_guild_configs()
        
    async def _initialize_guild_configs(self):
        """Sets up initial configuration for each guild the bot is in."""
        for guild in self.guilds:
            self.guild_configs[guild.id] = {
                'prefix': self.config.get('command_prefix', DEFAULT_PREFIX)
            }
            
    async def on_voice_state_update(self, member, before, after):
        """Event handler for voice state changes, handles auto-disconnect."""
        if member.bot:
            return
            
        if before.channel and not after.channel:
            voice_client = discord.utils.get(self.voice_clients, channel=before.channel)
            if not voice_client:
                return
                
            members = [m for m in before.channel.members if not m.bot]
            if not members:
                if voice_client.guild.id in self.players:
                    player = self.players[voice_client.guild.id]
                    player.queue.clear()
                    player.is_playing = False
                    player.current = None
                
                await voice_client.disconnect()

    def set_audio_quality(self, bitrate: int, sampling_rate: int, audio_channels: int):
        """Sets the preferred audio parameters for new streams."""
        valid_bitrate = 32 <= bitrate <= 320
        valid_sampling_rate = sampling_rate in [44100, 48000]
        valid_audio_channels = audio_channels in [1, 2]

        if valid_bitrate and valid_sampling_rate and valid_audio_channels:
            self.audio_bitrate = bitrate
            self.audio_sampling_rate = sampling_rate
            self.audio_channels = audio_channels
            logger.info(f"Audio parameters set: Bitrate {bitrate}kbps, SR {sampling_rate}Hz, Channels {audio_channels} for future streams.")
            return True
        
        error_messages = []
        if not valid_bitrate:
            error_messages.append(f"Invalid bitrate: {bitrate} (must be 32-320)")
        if not valid_sampling_rate:
            error_messages.append(f"Invalid sampling rate: {sampling_rate} (must be 44100 or 48000)")
        if not valid_audio_channels:
            error_messages.append(f"Invalid audio channels: {audio_channels} (must be 1 or 2)")
        logger.warning(f"Invalid audio parameters: {'; '.join(error_messages)}")
        return False
