import asyncio
import logging
import time
from typing import Dict, Any, Optional
from collections import deque
import yt_dlp
import discord
from .constants import YTDLP_OPTIONS_PLAYBACK, FFMPEG_OPTIONS_TEMPLATE

logger = logging.getLogger(__name__)

class MusicPlayer:
    """Manages the music queue and playback for a single guild."""
    def __init__(self, bot):
        """Initializes the player state, queue, and event loop."""
        self.bot = bot
        self.queue = deque(maxlen=1000)  
        self.current: Optional[Dict[str, Any]] = None
        self.is_playing = False
        self.is_paused = False
        self.start_time = None
        self.pause_time = None
        self._loop = asyncio.get_event_loop()

    async def play_next(self, ctx):
        """Plays the next song in the queue."""
        if not self.queue or not ctx.voice_client or not ctx.voice_client.is_connected():
            self.is_playing = False
            self.current = None
            return

        try:
            logger.debug("\n🎵 Intentando reproducir siguiente canción...")
            self.is_playing = True
            next_song = self.queue.popleft()
            self.current = next_song
            self.start_time = time.time()
            self.pause_time = None

            url = next_song.get('webpage_url')
            if not url:
                logger.error("❌ URL no encontrada en la información de la canción")
                raise ValueError("URL no encontrada en la información de la canción")
                
            logger.debug(f"🔗 URL a procesar: {url}")
            
            # Get current audio settings from bot config
            current_bitrate = self.bot.audio_bitrate
            current_sampling_rate = self.bot.audio_sampling_rate
            current_audio_channels = self.bot.audio_channels

            # Prepare YTDLP options (deep copy to avoid modifying global constant)
            current_ytdlp_options = YTDLP_OPTIONS_PLAYBACK.copy()
            # Opus is generally VBR, so preferredquality='0' is often best.
            # If a specific bitrate is desired with Opus, it's typically handled by FFmpeg.
            # Forcing it here might conflict or be ignored depending on yt-dlp version and Opus.
            # We will let FFmpeg handle the bitrate precisely.

            logger.debug("⚙️ Extrayendo información con yt-dlp...")
            with yt_dlp.YoutubeDL(current_ytdlp_options) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                if not info:
                    raise ValueError("No se pudo extraer la información del video")
                
                formats = info.get('formats', [])
                logger.debug(f"📋 Encontrados {len(formats)} formatos disponibles")
                
                audio_formats = [f for f in formats if f.get('acodec') != 'none']
                if not audio_formats:
                    raise ValueError("No se encontraron formatos de audio")
                
                best_audio = max(audio_formats, key=lambda f: f.get('abr', 0) if f.get('abr') else 0)
                stream_url = best_audio.get('url')
                
                if not stream_url:
                    raise ValueError("No se encontró URL de stream")
                
                logger.debug(f"✅ Formato seleccionado: {best_audio.get('format_id')} - {best_audio.get('acodec')} - {best_audio.get('abr')}kbps")
            
            logger.debug("🎧 Creando fuente de audio...")
            try:
                # Format FFMPEG options with the current settings
                bufsize = current_bitrate * 2 
                current_ffmpeg_options = {
                    'before_options': FFMPEG_OPTIONS_TEMPLATE['before_options'],
                    'options': FFMPEG_OPTIONS_TEMPLATE['options'].format(
                        bitrate=current_bitrate, 
                        bufsize=bufsize,
                        sampling_rate=current_sampling_rate,
                        audio_channels=current_audio_channels
                    )
                }

                source_task = asyncio.create_task(
                    discord.FFmpegOpusAudio.from_probe(
                        stream_url,
                        **current_ffmpeg_options, # Use formatted options
                        method='fallback'
                    )
                )
                source = await asyncio.wait_for(source_task, timeout=30.0)
            except asyncio.TimeoutError:
                logger.warning("⚠️ Timeout creando fuente de audio, reintentando...")
                raise ValueError("Timeout creando fuente de audio")
            
            def after_playing(error):
                if error:
                    logger.error(f"❌ Error después de reproducir: {error}")
                asyncio.run_coroutine_threadsafe(
                    self.handle_song_complete(ctx), 
                    self._loop
                )
            
            logger.debug("▶️ Iniciando reproducción...")
            ctx.voice_client.play(source, after=after_playing)
            await ctx.send(f"🎵 Reproduciendo: {self.current['title']}")
            logger.info(f"✅ Reproducción iniciada: {self.current['title']}")
            
        except Exception as e:
            logger.error(f"❌ Error en play_next: {str(e)}")
            self.is_playing = False
            self.current = None
            await asyncio.sleep(2)
            await self.play_next(ctx)

    async def handle_song_complete(self, ctx):
        """Called when a song finishes; plays the next or stops if queue is empty."""
        if self.queue:
            await self.play_next(ctx)
        else:
            self.is_playing = False
            self.current = None

    def get_current_duration(self) -> str:
        """Returns the formatted current playback time and total duration."""
        if not self.current:
            return "0:00/0:00"
            
        total_duration = int(float(self.current.get('duration', 0)))
        
        if self.pause_time:
            current_time = int(self.pause_time - self.start_time)
        else:
            current_time = int(time.time() - self.start_time)
            
        return f"{self.format_duration(current_time)}/{self.format_duration(total_duration)}"

    @staticmethod
    def format_duration(duration: int) -> str:
        """Formats a duration in seconds into H:MM:SS or M:SS format."""
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}" 