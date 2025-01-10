import logging
import os
import sys
from src.core import MusicBot

def resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def main():
    try:
        logger.info("Iniciando Music Bot...")
        # Asegurarse de que estamos en el directorio correcto
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        bot = MusicBot()
        bot.run(bot.discord_token)
    except Exception as e:
        logger.exception(f"Error al iniciar el bot: {e}")

if __name__ == "__main__":
    main()
