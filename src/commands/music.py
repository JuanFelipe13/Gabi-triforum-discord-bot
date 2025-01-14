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
