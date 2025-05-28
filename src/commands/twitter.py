from discord.ext import commands
import discord
import re
import logging
import yt_dlp
import asyncio
import os
from typing import Dict, Optional, List, Tuple
import requests

logger = logging.getLogger(__name__)

TWITTER_DOMAINS = ('twitter.com', 'x.com', 'fxtwitter.com')
YOUTUBE_DOMAINS = ('youtube.com', 'youtu.be')
TWITTER_REGEX = re.compile(
    r'https?:\/\/(?:www\.)?(?:twitter\.com|x\.com|fxtwitter\.com)\/(?:#!\/)?(\w+)\/status(?:es)?\/(\d+)'
)
YOUTUBE_REGEX = re.compile(
    r'(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/)|youtu\.be\/)([a-zA-Z0-9_-]{11})'
)

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB en bytes

class TwitterCommands(commands.Cog):
    """Cog for handling Twitter/X link detection and media embedding."""
    def __init__(self, bot):
        """Initializes the TwitterCommands cog and active channel tracking."""
        self.bot = bot
        self.active_channels: Dict[int, bool] = {}
        
    async def download_tweet_media(self, url: str) -> List[Tuple[str, str]]:
        """Attempts to extract direct media URLs (video) from a Twitter/X or YouTube link."""
        try:
            logger.debug(f"URL original: {url}")
            
            # Convert Twitter URL to proper format
            if '@' in url:
                url = url.replace('@', 'https://')
            elif not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            
            logger.debug(f"URL después de formato básico: {url}")
            
            # Extract tweet ID
            tweet_id = None
            if 'twitter.com' in url or 'x.com' in url:
                # Extract ID from Twitter URL
                parts = url.split('/status/')
                if len(parts) > 1:
                    tweet_id = parts[1].split('/')[0].split('?')[0]
                    logger.debug(f"ID de tweet extraído: {tweet_id}")
                    
                    # Use TW-Down API for Twitter
                    api_url = f"https://twdown.net/download.php?type=videos&url=https://twitter.com/i/status/{tweet_id}"
                    logger.debug(f"Usando TW-Down API: {api_url}")
                    
                    # Get the page content
                    response = await asyncio.to_thread(requests.get, api_url)
                    
                    if response.status_code == 200:
                        html_content = response.text
                        
                        # Look for direct video URLs
                        video_url_pattern = r'href=[\'"]?([^\'" >]+\.mp4)[\'"]?'
                        video_matches = re.findall(video_url_pattern, html_content)
                        
                        if video_matches:
                            best_url = video_matches[0]  # Get first match
                            logger.debug(f"URL de video encontrado: {best_url}")
                            return [('video', best_url)]
                            
            # If Twitter video extraction fails or URL is YouTube, try with yt-dlp
            logger.debug(f"Usando yt-dlp para extraer video...")
            # Configurar yt-dlp con opciones optimizadas
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
                'force_generic_extractor': False,
                'ignoreerrors': True,
                'nocheckcertificate': True,
                'logtostderr': False,
                'no_color': True,
                'retries': 10,
                'fragment_retries': 10,
                'skip_download': True
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, download=False)
                
                if not info:
                    logger.debug("No se encontró información para el URL proporcionado.")
                    return []
                
                logger.debug(f"Información extraída: {info.get('title', 'Sin título')}")
                
                # Buscar el mejor formato de video
                media_urls = []
                
                if 'formats' in info:
                    formats = info['formats']
                    logger.debug(f"Encontrados {len(formats)} formatos")
                    
                    # Filtrar por formatos de video MP4
                    video_formats = [f for f in formats if 
                                  f.get('ext') == 'mp4' and 
                                  f.get('vcodec') != 'none']
                    
                    if video_formats:
                        # Ordenar por calidad (tamaño, ancho, etc.)
                        best_format = max(video_formats, 
                                         key=lambda x: (
                                             x.get('width', 0) * x.get('height', 0),
                                             x.get('tbr', 0)
                                         ))
                        
                        logger.debug(f"Mejor formato encontrado: {best_format.get('format_id')}, "
                              f"resolución: {best_format.get('width')}x{best_format.get('height')}")
                        
                        media_urls.append(('video', best_format['url']))
                
                # Si no hay formatos, intentar obtener el URL directo
                if not media_urls and 'url' in info:
                    logger.debug(f"Usando URL directo del video")
                    media_urls.append(('video', info['url']))
                    
                if not media_urls:
                    logger.debug("No se encontraron videos en el contenido.")
                    return []
                    
                return media_urls
                
        except Exception as e:
            logger.error(f"Error descargando medios: {e}, Tipo: {type(e)}")
            return []

    async def download_video(self, url: str) -> Optional[str]:
        """Downloads a video from a direct URL to a temporary file."""
        try:
            logger.debug(f"Intentando descargar video desde URL: {url}")
            # Crear directorio temporal si no existe
            os.makedirs('temp', exist_ok=True)
            
            # Generar nombre único para el archivo
            filename = f"temp/video_{hash(url)}.mp4"
            
            # Descargar el video usando requests
            response = await asyncio.to_thread(requests.get, url, stream=True)
            
            if response.status_code != 200:
                logger.error(f"Error descargando video: {response.status_code}")
                return None
            
            # Guardar el video
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Verificar tamaño del archivo
            file_size = os.path.getsize(filename)
            if file_size > MAX_FILE_SIZE:
                logger.warning(f"Video demasiado grande ({file_size / 1024 / 1024:.1f} MB)")
                os.remove(filename)
                return None
            
            return filename
            
        except Exception as e:
            logger.error(f"Error descargando video: {e}")
            return None
        
    async def cleanup_temp_file(self, filepath: str):
        """Safely removes a temporary file if it exists."""
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            logger.error(f"Error eliminando archivo temporal: {e}")

    @commands.command()
    async def twitter(self, ctx, option: str = None):
        """Toggles automatic Twitter/X video embedding for the current channel or shows status."""
        if option is None:
            status = "activado" if self.active_channels.get(ctx.channel.id, False) else "desactivado"
            await ctx.send(f"📱 El detector de tweets está {status} en este canal")
            return
            
        option = option.lower()
        if option not in ['on', 'off']:
            await ctx.send("❌ Opciones válidas: on/off")
            return
            
        self.active_channels[ctx.channel.id] = (option == 'on')
        status = "activado" if option == 'on' else "desactivado"
        await ctx.send(f"📱 Detector de tweets {status} en este canal")

    @commands.Cog.listener()
    async def on_message(self, message):
        """Listener that checks messages for Twitter/X links and attempts to embed videos."""
        if message.author.bot:
            return
            
        if not self.active_channels.get(message.channel.id, False):
            return
            
        # Check for Twitter URLs
        twitter_matches = TWITTER_REGEX.finditer(message.content)
        youtube_matches = YOUTUBE_REGEX.finditer(message.content)
        
        matches = list(twitter_matches) + list(youtube_matches)
        
        for match in matches:
            try:
                url = match.group(0)
                async with message.channel.typing():
                    media_urls = await self.download_tweet_media(url)
                    
                    if not media_urls:
                        continue
                    
                    for media_type, url in media_urls:
                        if media_type == 'video':
                            video_path = await self.download_video(url)
                            if video_path:
                                try:
                                    await message.channel.send(
                                        content=f"🎥 Compartido por {message.author.display_name}",
                                        file=discord.File(video_path, filename="video.mp4")
                                    )
                                except discord.HTTPException as e:
                                    logger.error(f"Error enviando video: {e}")
                                    await message.channel.send(
                                        f"⚠️ El video es demasiado grande para enviarlo directamente. "
                                        f"Puedes verlo aquí: {url}"
                                    )
                                finally:
                                    await self.cleanup_temp_file(video_path)
                            else:
                                await message.channel.send(
                                    f"⚠️ El video es demasiado grande para enviarlo directamente. "
                                    f"Puedes verlo aquí: {url}"
                                )
                            
                    try:
                        await message.delete()
                    except discord.errors.Forbidden:
                        logger.warning("No se pudo borrar el mensaje original - Permisos insuficientes")
                            
            except Exception as e:
                logger.error(f"Error procesando video: {e}")
                await message.channel.send("❌ Error procesando el video")