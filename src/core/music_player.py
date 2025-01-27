import asyncio
import logging
import time
from typing import Dict, Any, Optional
from collections import deque
from functools import lru_cache
import yt_dlp
import discord
from .constants import YTDLP_OPTIONS, FFMPEG_OPTIONS

logger = logging.getLogger(__name__)

class MusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.queue = deque(maxlen=1000)  
        self.current: Optional[Dict[str, Any]] = None
        self.is_playing = False
        self.is_paused = False
        self.start_time = None
        self.pause_time = None
        self._loop = asyncio.get_event_loop()

    @lru_cache(maxsize=100)
    async def _get_stream_url(self, url: str) -> Optional[str]:
        try:
            with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                if info:
                    return info.get('url')
                return None
        except Exception as e:
            logger.error(f"Error obteniendo stream URL: {e}")
            return None

    async def play_next(self, ctx):
        if not self.queue or not ctx.voice_client or not ctx.voice_client.is_connected():
            self.is_playing = False
            self.current = None
            return

        try:
            self.is_playing = True
            next_song = self.queue.popleft()
            self.current = next_song
            self.start_time = time.time()
            self.pause_time = None

            url = next_song.get('webpage_url')
            stream_url = await self._get_stream_url(url)
            
            if not stream_url:
                raise ValueError("No se pudo obtener la URL del stream")

            source = await discord.FFmpegOpusAudio.from_probe(
                stream_url,
                **FFMPEG_OPTIONS,
                method='fallback'
            )
            
            def after_playing(error):
                if error:
                    logger.error(f"Error después de reproducir: {error}")
                asyncio.run_coroutine_threadsafe(
                    self.handle_song_complete(ctx), 
                    self._loop
                )
            
            ctx.voice_client.play(source, after=after_playing)
            await ctx.send(f"🎵 Reproduciendo: {self.current['title']}")
            
        except Exception as e:
            logger.error(f"Error reproduciendo siguiente canción: {e}")
            self.is_playing = False
            self.current = None
            await self.play_next(ctx)

    async def handle_song_complete(self, ctx):
        if self.queue:
            await self.play_next(ctx)
        else:
            self.is_playing = False
            self.current = None

    def get_current_duration(self) -> str:
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
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = int(duration % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}" 