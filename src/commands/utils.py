from discord.ext import commands
import discord
import logging
from ..core import MusicPlayer, URL_REGEX, YTDLP_OPTIONS_PLAYLIST_INFO, YTDLP_OPTIONS_PLAYBACK, YTDLP_SEARCH_OPTIONS
import yt_dlp
import asyncio
from typing import Dict
import time

logger = logging.getLogger(__name__)

def get_player(ctx, bot) -> MusicPlayer:
    """Gets or creates the MusicPlayer instance for the given guild."""
    guild_id = ctx.guild.id
    if guild_id not in bot.players:
        bot.players[guild_id] = MusicPlayer(bot)
    return bot.players[guild_id]

async def handle_search(ctx, query: str, player):
    """Performs a YouTube search, displays results, and handles user selection."""
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

            logger.debug(f"Número de entradas de búsqueda encontradas: {len(info.get('entries', []))}")
            results = []
            for entry in list(info['entries'])[:5]:
                if entry:
                    results.append({
                        'title': entry.get('title', 'No disponible'),
                        'webpage_url': entry.get('url')
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

            view = discord.ui.View(timeout=30.0)
            selected_url = None

            async def button_callback(interaction: discord.Interaction, url: str):
                nonlocal selected_url
                if interaction.user != ctx.author:
                    await interaction.response.send_message("No puedes usar esta interacción.", ephemeral=True)
                    return
                selected_url = url
                await interaction.response.defer() # Acknowledge interaction
                view.stop() # Stop the view from listening to further interactions

            async def cancel_callback(interaction: discord.Interaction):
                nonlocal selected_url
                if interaction.user != ctx.author:
                    await interaction.response.send_message("No puedes usar esta interacción.", ephemeral=True)
                    return
                selected_url = "CANCEL"
                await interaction.response.defer()
                view.stop()

            for i, result_entry in enumerate(results):
                button = discord.ui.Button(label=f"{i+1}", style=discord.ButtonStyle.primary, custom_id=f"select_{i}")
                
                # Need to use a wrapper or lambda with default argument to capture current result_entry['webpage_url']
                async def make_callback(url_to_select):
                    async def callback(interaction: discord.Interaction):
                        await button_callback(interaction, url_to_select)
                    return callback

                button.callback = await make_callback(result_entry['webpage_url'])
                view.add_item(button)
            
            cancel_button = discord.ui.Button(label="Cancelar", style=discord.ButtonStyle.danger, custom_id="cancel_search")
            cancel_button.callback = cancel_callback
            view.add_item(cancel_button)
            
            embed.set_footer(text="Selecciona una canción usando los botones o cancela.")
            message = await ctx.send(embed=embed, view=view)
            
            # Wait for the view to stop (either by interaction or timeout)
            await view.wait()

            if view.is_finished() and hasattr(message, 'delete'): # Check if message exists before deleting
                try:
                    await message.delete()
                except discord.NotFound:
                    logger.warn("Mensaje de búsqueda ya fue eliminado o no encontrado al intentar borrar.")
                except Exception as e:
                    logger.error(f"Error al eliminar mensaje de búsqueda: {e}")


            if selected_url and selected_url != "CANCEL":
                await handle_url(ctx, selected_url, player)
            # elif selected_url == "CANCEL" or (view.is_finished() and selected_url is None): # Timeout or explicit cancel
            #     # Message already deleted or will be by finally block if interaction happened
            #     # If it was a timeout, selected_url is None
            #     pass # No action needed if cancelled or timed out, message is handled

            # No need for the old reaction logic or explicit finally delete for the message
            # as the view handles timeout and button presses manage the message lifecycle or response.

    except Exception as e:
        logger.error(f"Error en handle_search: {e}")
        await ctx.send("❌ Error procesando la búsqueda")

async def handle_url(ctx, url, player):
    """Processes a URL (song or playlist), extracts info, and adds to the queue."""
    try:
        with yt_dlp.YoutubeDL(YTDLP_OPTIONS_PLAYLIST_INFO) as ydl:
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
                        'webpage_url': entry.get('webpage_url', url),
                        'title': entry.get('title', 'No disponible'),
                        'duration': entry.get('duration', 0)
                    }
                    player.queue.append(song_info)

            else:
                song_info = {
                    'webpage_url': info.get('webpage_url', url),
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
    """Attempts to extract the duration (in seconds) from yt-dlp video info."""
    try:
        if isinstance(video_info, dict):
            if 'duration' in video_info:
                return int(float(video_info['duration']))
            
            if '_type' in video_info and video_info['_type'] == 'url' and 'url' in video_info:
                try:
                    with yt_dlp.YoutubeDL(YTDLP_OPTIONS_PLAYBACK) as ydl:
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
