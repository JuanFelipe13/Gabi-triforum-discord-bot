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
        max_retries = 3
        retry_count = 0
        
        print(f"🔍 Intentando obtener stream URL para: {url}")
        
        while retry_count < max_retries:
            try:
                print(f"📥 Intento {retry_count + 1}/{max_retries} de extracción...")
                with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
                    print("⚙️ Iniciando extracción de información...")
                    info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                    if info:
                        print("✅ Información extraída correctamente")
                        # Intentar obtener la mejor URL de audio
                        formats = info.get('formats', [])
                        if formats:
                            print(f"📋 Buscando en {len(formats)} formatos disponibles...")
                            # Filtrar formatos de audio
                            audio_formats = [f for f in formats if f.get('acodec') != 'none']
                            if audio_formats:
                                # Seleccionar el mejor formato de audio
                                best_audio = max(audio_formats, key=lambda f: f.get('abr', 0) if f.get('abr') else 0)
                                stream_url = best_audio.get('url')
                                if stream_url:
                                    print(f"🎯 URL encontrada en formato de audio: {best_audio.get('format_id', 'unknown')}")
                                    return stream_url
                        
                        # Si no se encontró en los formatos, intentar obtener la URL directamente
                        stream_url = info.get('url')
                        if stream_url:
                            print("🎯 URL de stream encontrada directamente")
                            return stream_url
                    print("❌ No se encontró ninguna URL válida en la información")
                    return None
            except Exception as e:
                print(f"⚠️ Error en intento {retry_count + 1}: {str(e)}")
                logger.error(f"Intento {retry_count + 1}/{max_retries} falló: {e}")
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = 2 ** retry_count
                    print(f"⏳ Esperando {wait_time} segundos antes del siguiente intento...")
                    await asyncio.sleep(wait_time)
                continue
        
        print("❌ Todos los intentos de obtener la URL fallaron")
        logger.error(f"Error obteniendo stream URL después de {max_retries} intentos")
        return None

    async def play_next(self, ctx):
        if not self.queue or not ctx.voice_client or not ctx.voice_client.is_connected():
            self.is_playing = False
            self.current = None
            return

        try:
            print("\n🎵 Intentando reproducir siguiente canción...")
            self.is_playing = True
            next_song = self.queue.popleft()
            self.current = next_song
            self.start_time = time.time()
            self.pause_time = None

            url = next_song.get('webpage_url')
            if not url:
                print("❌ URL no encontrada en la información de la canción")
                raise ValueError("URL no encontrada en la información de la canción")
                
            print(f"🔗 URL a procesar: {url}")
            
            # Intentar obtener el stream directamente con yt-dlp
            try:
                print("⚙️ Extrayendo información con yt-dlp...")
                with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
                    info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                    if not info:
                        raise ValueError("No se pudo extraer la información del video")
                    
                    # Intentar obtener la mejor URL de audio
                    formats = info.get('formats', [])
                    print(f"📋 Encontrados {len(formats)} formatos disponibles")
                    
                    # Filtrar formatos de audio y ordenarlos por calidad
                    audio_formats = [f for f in formats if f.get('acodec') != 'none']
                    if not audio_formats:
                        raise ValueError("No se encontraron formatos de audio")
                    
                    # Seleccionar el mejor formato de audio
                    best_audio = max(audio_formats, key=lambda f: f.get('abr', 0) if f.get('abr') else 0)
                    stream_url = best_audio.get('url')
                    
                    if not stream_url:
                        raise ValueError("No se encontró URL de stream")
                    
                    print(f"✅ Formato seleccionado: {best_audio.get('format_id')} - {best_audio.get('acodec')} - {best_audio.get('abr')}kbps")
            
            except Exception as e:
                print(f"❌ Error extrayendo información: {e}")
                raise

            print("🎧 Creando fuente de audio...")
            try:
                # Intentar crear la fuente de audio con timeout
                source_task = asyncio.create_task(
                    discord.FFmpegOpusAudio.from_probe(
                        stream_url,
                        **FFMPEG_OPTIONS,
                        method='fallback'
                    )
                )
                source = await asyncio.wait_for(source_task, timeout=30.0)
            except asyncio.TimeoutError:
                print("⚠️ Timeout creando fuente de audio, reintentando...")
                raise ValueError("Timeout creando fuente de audio")
            
            def after_playing(error):
                if error:
                    print(f"❌ Error después de reproducir: {error}")
                    logger.error(f"Error después de reproducir: {error}")
                asyncio.run_coroutine_threadsafe(
                    self.handle_song_complete(ctx), 
                    self._loop
                )
            
            print("▶️ Iniciando reproducción...")
            ctx.voice_client.play(source, after=after_playing)
            await ctx.send(f"🎵 Reproduciendo: {self.current['title']}")
            print(f"✅ Reproducción iniciada: {self.current['title']}")
            
        except Exception as e:
            print(f"❌ Error en play_next: {str(e)}")
            logger.error(f"Error reproduciendo siguiente canción: {e}")
            self.is_playing = False
            self.current = None
            # Esperar un momento antes de intentar la siguiente canción
            await asyncio.sleep(2)
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