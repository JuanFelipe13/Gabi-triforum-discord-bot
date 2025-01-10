from discord.ext import commands
import discord
import logging
import yt_dlp
import asyncio
from collections import deque
import re

logger = logging.getLogger(__name__)

# YT-DLP config
YTDLP_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'extract_flat': 'in_playlist'
}

# URL pattern
URL_REGEX = r'https?://(?:www\.)?.+'

# Music player class
class MusicPlayer:
    def __init__(self, bot):
        self.bot = bot
        self.queue = deque()
        self.current = None
        self.is_playing = False
        self._loop = asyncio.get_event_loop()

    async def play_next(self, ctx):
        if self.queue and ctx.voice_client and ctx.voice_client.is_connected():
            try:
                self.is_playing = True
                self.current = self.queue.popleft()
                
                with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
                    info = await asyncio.to_thread(
                        ydl.extract_info,
                        self.current.get('webpage_url') or self.current.get('url'),
                        download=False
                    )
                    if not info:
                        raise ValueError("No se pudo obtener información del video")
                    
                    stream_url = info.get('url') or info.get('webpage_url')
                    if not stream_url:
                        raise ValueError("No se pudo obtener la URL del stream")
                
                source = await discord.FFmpegOpusAudio.from_probe(
                    stream_url,
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
                    options="-vn"
                )
                
                def after_playing(error):
                    if error:
                        logger.error(f"Error después de reproducir: {error}")
                    self._loop.create_task(self.handle_song_complete(ctx))
                
                ctx.voice_client.play(source, after=after_playing)
                await ctx.send(f"🎵 Reproduciendo: {self.current['title']}")
            except Exception as e:
                logger.error(f"Error reproduciendo siguiente canción: {e}")
                self.is_playing = False
                self.current = None
                await self.play_next(ctx)
        else:
            self.is_playing = False
            self.current = None
            
    async def handle_song_complete(self, ctx):
        if self.queue:
            await self.play_next(ctx)
        else:
            self.is_playing = False
            self.current = None
            await ctx.send("📋 Cola de reproducción terminada")

# Setup commands
def setup_commands(bot):
    players = {}
    
    def get_player(ctx):
        if ctx.guild.id not in players:
            players[ctx.guild.id] = MusicPlayer(bot)
        return players[ctx.guild.id]

    # Voice commands
    @bot.command()
    async def join(ctx):
        if ctx.author.voice:
            channel = ctx.author.voice.channel
            if ctx.voice_client:
                await ctx.voice_client.move_to(channel)
            else:
                await channel.connect()
            await ctx.send(f"¡Me uní al canal {channel}!")
        else:
            await ctx.send("¡Necesitas estar en un canal de voz!")

    # Music playback
    @bot.command()
    async def play(ctx, *, query):
        player = get_player(ctx)
        
        try:
            if not ctx.voice_client:
                if ctx.author.voice:
                    await ctx.author.voice.channel.connect()
                else:
                    await ctx.send("¡Necesitas estar en un canal de voz!")
                    return

            async with ctx.typing():
                if not re.match(URL_REGEX, query):
                    search_opts = YTDLP_OPTIONS.copy()
                    search_opts['default_search'] = 'ytsearch5'
                    
                    with yt_dlp.YoutubeDL(search_opts) as ydl:
                        try:
                            info = await asyncio.to_thread(ydl.extract_info, query, download=False)
                            if not info.get('entries'):
                                await ctx.send("❌ No se encontraron resultados")
                                return
                            
                            embed = discord.Embed(
                                title="🔍 Resultados de búsqueda",
                                description="Reacciona con el número para seleccionar una canción:",
                                color=discord.Color.blue()
                            )
                            
                            for idx, entry in enumerate(info['entries'][:5], 1):
                                embed.add_field(
                                    name=f"{idx}. {entry.get('title', 'No disponible')}",
                                    value=f"Duración: {entry.get('duration_string', 'N/A')}",
                                    inline=False
                                )
                            
                            message = await ctx.send(embed=embed)
                            reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
                            
                            for reaction in reactions[:len(info['entries'])]:
                                await message.add_reaction(reaction)
                            
                            def check(reaction, user):
                                return user == ctx.author and str(reaction.emoji) in reactions
                            
                            try:
                                reaction, user = await bot.wait_for('reaction_add', timeout=30.0, check=check)
                                selected_idx = reactions.index(str(reaction.emoji))
                                selected_video = info['entries'][selected_idx]
                                
                                player.queue.append({
                                    'webpage_url': selected_video.get('webpage_url') or selected_video.get('url'),
                                    'url': selected_video.get('url'),
                                    'title': selected_video.get('title', 'No disponible')
                                })

                                await message.delete()
                                await ctx.send(f"✅ Agregado a la cola: {selected_video['title']}")
                                
                                if not player.is_playing:
                                    await player.play_next(ctx)
                                    
                            except asyncio.TimeoutError:
                                await message.delete()
                                await ctx.send("❌ Tiempo de selección agotado")
                                return
                            
                        except Exception as e:
                            logger.error(f"Error en la búsqueda: {e}")
                            await ctx.send("❌ Error realizando la búsqueda")
                            return
                else:
                    with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
                        try:
                            info = await asyncio.to_thread(ydl.extract_info, query, download=False)
                            
                            if 'entries' in info:
                                entries = info['entries']
                                await ctx.send(f"⏳ Procesando playlist con {len(entries)} videos...")
                                
                                detailed_options = YTDLP_OPTIONS.copy()
                                detailed_options['extract_flat'] = False
                                
                                with yt_dlp.YoutubeDL(detailed_options) as detailed_ydl:
                                    for entry in entries:
                                        if entry:
                                            try:
                                                video_url = entry.get('url') or entry.get('webpage_url')
                                                if not video_url:
                                                    continue
                                                    
                                                video_info = await asyncio.to_thread(
                                                    detailed_ydl.extract_info,
                                                    video_url,
                                                    download=False
                                                )
                                                
                                                player.queue.append({
                                                    'webpage_url': video_info.get('webpage_url') or video_info.get('url'),
                                                    'url': video_info.get('url'),
                                                    'title': video_info.get('title', 'No disponible')
                                                })
                                            except Exception as e:
                                                logger.error(f"Error procesando video de playlist: {e}")
                                                continue
                                
                                await ctx.send(f"📋 {len(player.queue)} canciones agregadas a la cola")
                            else:
                                player.queue.append({
                                    'webpage_url': info.get('webpage_url'),
                                    'title': info.get('title', 'No disponible')
                                })
                                await ctx.send("✅ Canción agregada a la cola")
                            
                            if not player.is_playing:
                                await player.play_next(ctx)
                                
                        except Exception as e:
                            logger.error(f"Error procesando URL: {e}")
                            await ctx.send("❌ Error procesando el video o playlist")
            
        except Exception as e:
            logger.exception(f"Error reproduciendo audio: {e}")
            await ctx.send("❌ Error reproduciendo el audio")

    # Queue management
    @bot.command()
    async def skip(ctx):
        player = get_player(ctx)
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Saltando a la siguiente canción...")
        else:
            await ctx.send("❌ No hay nada reproduciéndose")

    @bot.command()
    async def queue(ctx):
        player = get_player(ctx)
        if not player.queue and not player.current:
            await ctx.send("📋 La cola está vacía")
            return
            
        embed = discord.Embed(title="Cola de Reproducción", color=discord.Color.blue())
        
        if player.current:
            embed.add_field(name="🎵 Reproduciendo ahora:", 
                          value=player.current['title'], 
                          inline=False)
        
        if player.queue:
            queue_text = "\n".join(
                f"{i+1}. {song['title']}" 
                for i, song in enumerate(player.queue)
            )
            embed.add_field(name="📋 Siguientes:", 
                          value=queue_text if len(queue_text) <= 1024 else f"{queue_text[:1021]}...", 
                          inline=False)
        
        await ctx.send(embed=embed)

    @bot.command()
    async def clear(ctx):
        player = get_player(ctx)
        player.queue.clear()
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
        await ctx.send("🗑️ Cola limpiada")

    # Control commands
    @bot.command()
    async def leave(ctx):
        if ctx.voice_client:
            player = get_player(ctx)
            player.queue.clear()
            player.current = None
            player.is_playing = False
            await ctx.voice_client.disconnect()
            await ctx.send("¡Hasta luego!")

    @bot.command()
    async def pause(ctx):
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Pausado")
        
    @bot.command()
    async def resume(ctx):
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Reanudado")

    @bot.command()
    async def stop(ctx):
        player = get_player(ctx)
        player.queue.clear()
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            await ctx.send("⏹️ Detenido")

    # Help command
    @bot.command()
    async def ayuda(ctx):
        embed = discord.Embed(
            title="Comandos disponibles",
            description="Aquí tienes una lista de todos los comandos que puedes usar:",
            color=discord.Color.blue()
        )
        
        commands_list = [
            ("!join", "Unirse al canal de voz"),
            ("!play <query>", "Reproducir audio de YouTube (soporta URLs, playlists o términos de búsqueda)"),
            ("!skip", "Saltar a la siguiente canción"),
            ("!queue", "Ver la cola de reproducción"),
            ("!clear", "Limpiar la cola de reproducción"),
            ("!leave", "Salir del canal de voz"),
            ("!pause", "Pausar la reproducción"),
            ("!resume", "Reanudar la reproducción"),
            ("!stop", "Detener la reproducción"),
            ("!ayuda", "Mostrar todos los comandos disponibles"),
            ("!skip_to <position>", "Saltar a una canción específica en la cola")
        ]
        
        for command, description in commands_list:
            embed.add_field(name=command, value=description, inline=False)
        
        await ctx.send(embed=embed)

    # Skip to specific song
    @bot.command()
    async def skip_to(ctx, position: int):
        player = get_player(ctx)
        
        if not ctx.voice_client or not player.is_playing:
            await ctx.send("❌ No hay ninguna canción reproduciéndose.")
            return
        
        if position < 1 or position > len(player.queue):
            await ctx.send("❌ Posición inválida. Por favor, proporciona un número entre 1 y {}.".format(len(player.queue)))
            return
        
        player.current = player.queue[position - 1]
        player.queue = player.queue[:position - 1] + player.queue[position:]
        
        await ctx.send(f"⏭️ Saltando a: {player.current['title']}")
        await player.play_next(ctx)