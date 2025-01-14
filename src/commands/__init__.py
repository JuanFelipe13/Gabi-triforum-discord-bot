from .music import MusicCommands
from .playlist import PlaylistCommands

async def setup(bot):
    """Función requerida por discord.py para cargar la extensión"""
    await bot.add_cog(MusicCommands(bot))
    await bot.add_cog(PlaylistCommands(bot))