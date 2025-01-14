from discord.ext import commands
import discord
from ..core.playlist_manager import PlaylistManager
from ..core.music_player import MusicPlayer
from ..core.state import players
from .utils import get_player, URL_REGEX, YTDLP_OPTIONS, handle_url
import yt_dlp
import asyncio

class PlaylistCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.playlist_manager = PlaylistManager()

    @commands.command()
    async def createlist(self, ctx, name: str):
        if self.playlist_manager.create_playlist(ctx.author.id, name):
            await ctx.send(f"✅ Lista de reproducción '{name}' creada")
        else:
            await ctx.send("❌ Ya existe una lista con ese nombre")

    @commands.command()
    async def addtolist(self, ctx, name: str, *, query):
        try:
            with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
                if not URL_REGEX.match(query):
                    query = f"ytsearch:{query}"
                
                info = await asyncio.to_thread(ydl.extract_info, query, download=False)
                
                if 'entries' in info:
                    video = info['entries'][0]
                else:
                    video = info
                    
                song = {
                    'webpage_url': video.get('webpage_url'),
                    'title': video.get('title', 'No disponible')
                }
                
                if self.playlist_manager.add_to_playlist(ctx.author.id, name, song):
                    await ctx.send(f"✅ Añadida: {song['title']}")
                else:
                    await ctx.send("❌ Lista no encontrada")
                    
        except Exception:
            await ctx.send("❌ Error añadiendo la canción")

    @commands.command()
    async def removefromlist(self, ctx, name: str, index: int):
        if self.playlist_manager.remove_from_playlist(ctx.author.id, name, index):
            await ctx.send(f"✅ Canción {index} eliminada de '{name}'")
        else:
            await ctx.send("❌ Lista o índice no válido")

    @commands.command()
    async def showlist(self, ctx, name: str):
        playlist = self.playlist_manager.get_playlist(ctx.author.id, name)
        
        if not playlist:
            await ctx.send("❌ Lista no encontrada o vacía")
            return
            
        embed = discord.Embed(
            title=f"📋 Lista de reproducción: {name}",
            color=discord.Color.blue()
        )
        
        songs_text = "\n".join(
            f"{i+1}. {song['title']}" 
            for i, song in enumerate(playlist)
        )
        
        embed.add_field(
            name="Canciones:",
            value=songs_text[:1024] if len(songs_text) > 1024 else songs_text,
            inline=False
        )
        
        await ctx.send(embed=embed)

    @commands.command()
    async def playlist(self, ctx, name: str):
        player = get_player(ctx, players)
        playlist = self.playlist_manager.get_playlist(ctx.author.id, name)
        
        if not playlist:
            await ctx.send("❌ Lista no encontrada o vacía")
            return
            
        if not ctx.voice_client:
            if not ctx.author.voice:
                await ctx.send("¡Necesitas estar en un canal de voz!")
                return
            await ctx.author.voice.channel.connect()
        
        processing_msg = await ctx.send("⏳ Procesando playlist...")
        added_count = 0
        
        chunk_size = 5
        for i in range(0, len(playlist), chunk_size):
            chunk = playlist[i:i + chunk_size]
            tasks = [handle_url(ctx, song['webpage_url'], player) for song in chunk]
            
            try:
                await asyncio.gather(*tasks)
                added_count += len(chunk)
                await processing_msg.edit(
                    content=f"⏳ Procesando playlist... ({added_count}/{len(playlist)} canciones)"
                )
            except:
                continue
        
        await processing_msg.edit(
            content=f"✅ Playlist añadida: {added_count} canciones en cola"
        )
        
        if not player.is_playing:
            await player.play_next(ctx)

    @commands.command()
    async def mylists(self, ctx):
        playlists = self.playlist_manager.get_user_playlists(ctx.author.id)
        
        if not playlists:
            await ctx.send("❌ No tienes listas de reproducción")
            return
        
        embed = discord.Embed(
            title="📋 Tus listas de reproducción",
            description="\n".join(f"• {name}" for name in playlists),
            color=discord.Color.blue()
        )
        
        await ctx.send(embed=embed)
