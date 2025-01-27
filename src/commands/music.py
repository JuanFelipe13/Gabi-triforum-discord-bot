from discord.ext import commands
import discord
import logging
from ..core.music_player import MusicPlayer
from ..core.state import players
from .utils import get_player, handle_url, handle_search, URL_REGEX
import time

logger = logging.getLogger(__name__)

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def play(self, ctx, *, query=None):
        player = get_player(ctx, players)
        
        if query is None:
            if ctx.voice_client and ctx.voice_client.is_paused():
                ctx.voice_client.resume()
                player.is_paused = False
                player.pause_time = None
                await ctx.send("▶️ Reproducción reanudada")
                return
            elif ctx.voice_client and ctx.voice_client.is_playing():
                await ctx.send("▶️ Ya está reproduciéndose")
                return
            elif not player.queue:
                await ctx.send("❌ No hay nada en la cola para reproducir")
                return
            else:
                await player.play_next(ctx)
                return
        
        try:
            if not ctx.voice_client:
                if not ctx.author.voice:
                    await ctx.send("¡Necesitas estar en un canal de voz!")
                    return
                await ctx.author.voice.channel.connect()

            async with ctx.typing():
                if not URL_REGEX.match(query):
                    await handle_search(ctx, query, player)
                else:
                    await handle_url(ctx, query, player)
                    
        except Exception as e:
            logger.exception(f"Error reproduciendo audio: {e}")
            await ctx.send("❌ Error reproduciendo el audio")

    @commands.command()
    async def stop(self, ctx):
        player = get_player(ctx, players)
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            player.is_paused = True
            player.pause_time = time.time()
            await ctx.send("⏸️ Reproducción pausada")
        elif ctx.voice_client and ctx.voice_client.is_paused():
            await ctx.send("⏸️ La reproducción ya está pausada")
        else:
            await ctx.send("❌ No hay nada reproduciéndose")

    @commands.command()
    async def skip(self, ctx):
        player = get_player(ctx, players)
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Saltando a la siguiente canción")

    @commands.command()
    async def queue(self, ctx):
        player = get_player(ctx, players)
        
        logger.info(f"Queue status - current: {player.current}, queue length: {len(player.queue)}")
        
        if not player.current and len(player.queue) == 0:
            await ctx.send("📪 La cola está vacía")
            return
        
        embed = discord.Embed(title="🎵 Cola de Reproducción", color=discord.Color.blue())
        
        if player.current:
            current_duration = player.get_current_duration()
            logger.info(f"Current song: {player.current['title']} [{current_duration}]")
            embed.add_field(
                name="▶️ Reproduciendo ahora:",
                value=f"{player.current['title']} [{current_duration}]",
                inline=False
            )
        
        if player.queue:
            queue_text = "\n".join(
                f"{i+1}. {song['title']} [{player.format_duration(song.get('duration', 0))}]" 
                for i, song in enumerate(player.queue)
            )
            logger.info(f"Queue contents: {queue_text}")
            embed.add_field(
                name="📋 Próximas canciones:",
                value=queue_text[:1024] if len(queue_text) > 1024 else queue_text,
                inline=False
            )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def leave(self, ctx):
        player = get_player(ctx, players)
        
        if ctx.voice_client:
            player.queue.clear()
            player.is_playing = False
            player.current = None
            await ctx.voice_client.disconnect()
            await ctx.send("👋 ¡Hasta luego! Cola limpiada")

    @commands.command()
    async def resume(self, ctx):
        await self.play(ctx)

    @commands.command()
    async def remove(self, ctx, index: int):
        player = get_player(ctx, players)
        
        if not player.queue:
            await ctx.send("❌ La cola está vacía")
            return
        
        try:
            index = index - 1 
            if 0 <= index < len(player.queue):
                removed_song = player.queue.pop(index)
                await ctx.send(f"🗑️ Eliminada: {removed_song['title']}")
            else:
                await ctx.send("❌ Índice no válido")
        except ValueError:
            await ctx.send("❌ Por favor, proporciona un número válido")

    @commands.command()
    async def next(self, ctx, index: int):
        player = get_player(ctx, players)
        
        if not player.queue:
            await ctx.send("❌ La cola está vacía")
            return
        
        try:
            index = index - 1 
            if 0 <= index < len(player.queue):

                queue_list = list(player.queue)
                song = queue_list.pop(index)
                player.queue.clear()
                player.queue.appendleft(song)
                player.queue.extend(queue_list)
                await ctx.send(f"⏭️ Movida a siguiente: {song['title']}")
            else:
                await ctx.send("❌ Índice no válido")
        except ValueError:
            await ctx.send("❌ Por favor, proporciona un número válido")

    @commands.command()
    async def shuffle(self, ctx):
        player = get_player(ctx, players)
        
        if len(player.queue) < 2:
            await ctx.send("❌ No hay suficientes canciones en la cola para mezclar")
            return

        queue_list = list(player.queue)
        from random import shuffle
        shuffle(queue_list)
        
        player.queue.clear()
        player.queue.extend(queue_list)
        
        await ctx.send("🔀 Cola mezclada")

    @commands.command()
    async def playnow(self, ctx, *, query=None):
        if query is None:
            await ctx.send("❌ Por favor, proporciona una canción para reproducir")
            return
        
        player = get_player(ctx, players)
        
        try:
            if not ctx.voice_client:
                if not ctx.author.voice:
                    await ctx.send("¡Necesitas estar en un canal de voz!")
                    return
                await ctx.author.voice.channel.connect()
            
            async with ctx.typing():
                current_queue = player.queue.copy()
                player.queue.clear()
                
                if not URL_REGEX.match(query):
                    await handle_search(ctx, query, player)
                else:
                    await handle_url(ctx, query, player)
                
                if player.queue:
                    if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
                        ctx.voice_client.stop()
                    
                    player.queue.extend(current_queue)
                else:
                    player.queue.extend(current_queue)
                    await ctx.send("❌ No se pudo encontrar la canción")
                
        except Exception as e:
            logger.exception(f"Error reproduciendo audio: {e}")
            await ctx.send("❌ Error reproduciendo el audio")

    @commands.command()
    async def clean(self, ctx):
        player = get_player(ctx, players)

        player.queue.clear()
        
        if ctx.voice_client and (ctx.voice_client.is_playing() or ctx.voice_client.is_paused()):
            ctx.voice_client.stop()
            await ctx.send("🧹 Cola limpiada y canción actual saltada")
        else:
            await ctx.send("🧹 Cola limpiada")