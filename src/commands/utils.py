from discord.ext import commands
import discord
import logging
from ..core import MusicPlayer, URL_REGEX, YTDLP_OPTIONS, YTDLP_SEARCH_OPTIONS
import yt_dlp
import asyncio
from typing import Dict
import time

logger = logging.getLogger(__name__)

def get_player(ctx, players: Dict[int, MusicPlayer]) -> MusicPlayer:
    guild_id = ctx.guild.id
    if guild_id not in players:
        players[guild_id] = MusicPlayer(ctx.bot)
    return players[guild_id]

async def handle_search(ctx, query: str, player):
    try:
        with yt_dlp.YoutubeDL(YTDLP_SEARCH_OPTIONS) as ydl:
            search_query = f"ytsearch5:{query}"
            info = await asyncio.to_thread(
                ydl.extract_info,
                search_query,
                download=False
            )
            
            if not info or not info.get('entries'):
                await ctx.send("❌ No se encontraron resultados")
                return

            results = []
            for entry in list(info['entries'])[:5]:
                if entry:
                    results.append({
                        'title': entry.get('title', 'No disponible'),
                        'webpage_url': entry.get('url') or entry.get('webpage_url')
                    })

            if not results:
                await ctx.send("❌ No se encontraron resultados")
                return

            results_text = "\n".join(
                f"{i+1}. {entry['title']}" 
                for i, entry in enumerate(results)
            )
            
            embed = discord.Embed(
                title="🔍 Resultados de búsqueda",
                description=results_text,
                color=discord.Color.blue()
            )
            embed.set_footer(text="Reacciona con el número para seleccionar o ❌ para cancelar")
            
            message = await ctx.send(embed=embed)
            reactions = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '❌']
            
            await asyncio.gather(*[message.add_reaction(reaction) for reaction in reactions])
            
            try:
                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) in reactions
                
                reaction, user = await ctx.bot.wait_for(
                    'reaction_add',
                    timeout=30.0,
                    check=check
                )
                
                if str(reaction.emoji) == '❌':
                    await message.delete()
                    return
                
                choice = reactions.index(str(reaction.emoji))
                if choice < len(results):
                    selected = results[choice]
                    await message.delete()
                    await handle_url(ctx, selected['webpage_url'], player)
                
            except asyncio.TimeoutError:
                await message.delete()
            finally:
                try:
                    if not message.deleted:
                        await message.delete()
                except:
                    pass
                    
    except Exception as e:
        logger.error(f"Error en handle_search: {e}")
        await ctx.send("❌ Error procesando la búsqueda")

async def handle_url(ctx, url, player):
    try:
        with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
            info = await asyncio.to_thread(ydl.extract_info, url, download=False)
            
            if 'entries' in info:
                entries = info['entries']
                if not entries:
                    await ctx.send("❌ No se encontraron videos en la playlist")
                    return

                for entry in entries:
                    if not entry:
                        continue
                    song_info = {
                        'webpage_url': entry.get('url') or entry.get('webpage_url'),
                        'title': entry.get('title', 'No disponible'),
                        'duration': entry.get('duration', 0)
                    }
                    player.queue.append(song_info)

            else:
                song_info = {
                    'webpage_url': info.get('url') or info.get('webpage_url'),
                    'title': info.get('title', 'No disponible'),
                    'duration': info.get('duration', 0)
                }
                player.queue.append(song_info)

            if not player.is_playing:
                await player.play_next(ctx)

    except Exception as e:
        logger.error(f"Error en handle_url: {e}")
        await ctx.send("❌ Error procesando el URL")

def get_video_duration(video_info: dict) -> int:
    try:
        if isinstance(video_info, dict):
            if 'duration' in video_info:
                return int(float(video_info['duration']))
            
            if '_type' in video_info and video_info['_type'] == 'url' and 'url' in video_info:
                try:
                    with yt_dlp.YoutubeDL(YTDLP_OPTIONS) as ydl:
                        detailed_info = ydl.extract_info(video_info['url'], download=False)
                        if detailed_info and 'duration' in detailed_info:
                            return int(float(detailed_info['duration']))
                except Exception as e:
                    logger.error(f"Error obteniendo info detallada: {e}")
            
            formats = video_info.get('formats', [])
            if formats:
                for format_info in formats:
                    if isinstance(format_info, dict) and 'duration' in format_info:
                        return int(float(format_info['duration']))
        
        return 0
        
    except Exception as e:
        logger.error(f"Error procesando duración: {e}")
        return 0
