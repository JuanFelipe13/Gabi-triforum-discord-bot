import os
import threading
import json
import requests
from flask import Flask, render_template, request, jsonify
import yt_dlp
from ..core.constants import YTDLP_SEARCH_OPTIONS
from ..core.playlist_manager import PlaylistManager
import logging

logger = logging.getLogger(__name__)

def create_app(bot=None):
    """Creates and configures the Flask web application."""
    app = Flask(__name__)
    app.config['bot'] = bot
    playlist_manager = PlaylistManager()
    
    @app.route('/')
    def index():
        """Serves the main HTML page."""
        return render_template('index.html')
    
    @app.route('/api/status')
    def status():
        """Obtener el estado del bot"""
        if app.config['bot'] is None:
            return jsonify({"error": "Bot no disponible"}), 404
            
        status_data = {
            "connected": app.config['bot'].is_ready(),
            "guilds": len(app.config['bot'].guilds),
            "uptime": "Desconocido"
        }
        return jsonify(status_data)
    
    @app.route('/api/playlists')
    def playlists():
        """Obtener todas las listas de reproducción"""
        all_playlists = playlist_manager.playlists
        return jsonify(all_playlists)
    
    @app.route('/api/search')
    def search():
        """Buscar canciones en YouTube"""
        query = request.args.get('q', '')
        if not query:
            return jsonify({"error": "Consulta vacía"}), 400
            
        try:
            search_url = f"ytsearch5:{query}"
            with yt_dlp.YoutubeDL(YTDLP_SEARCH_OPTIONS) as ydl:
                info = ydl.extract_info(search_url, download=False)
                
            if not info or 'entries' not in info:
                return jsonify([])
                
            results = []
            for entry in info['entries']:
                if entry:
                    results.append({
                        "title": entry.get('title', 'Sin título'),
                        "url": entry.get('url', ''),
                        "webpage_url": entry.get('webpage_url', ''),
                        "thumbnail": entry.get('thumbnail', ''),
                        "duration": entry.get('duration', 0),
                        "channel": entry.get('channel', 'Desconocido')
                    })
            
            return jsonify(results)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/playlist/add', methods=['POST'])
    def add_to_playlist():
        """Añadir una canción a una playlist"""
        data = request.json
        
        if not data:
            return jsonify({"error": "Datos no proporcionados"}), 400
            
        playlist_name = data.get('playlist')
        song_data = data.get('song')
        
        if not playlist_name or not song_data:
            return jsonify({"error": "Nombre de lista o canción no especificado"}), 400

        WEB_USER_ID = 0

        if not playlist_manager.get_playlist(WEB_USER_ID, playlist_name):
            playlist_manager.create_playlist(WEB_USER_ID, playlist_name)

        existing_playlist_songs = playlist_manager.get_playlist(WEB_USER_ID, playlist_name)
        song_exists = any(s.get('title') == song_data.get('title') for s in existing_playlist_songs)

        if not song_exists:
            if playlist_manager.add_to_playlist(WEB_USER_ID, playlist_name, song_data):
                return jsonify({"success": True, "message": f"Canción añadida a la lista {playlist_name}"})
            else:
                return jsonify({"error": "Error añadiendo canción a la lista"}), 500
        else:
            return jsonify({"success": False, "message": "La canción ya existe en la lista"})
                
    @app.route('/api/audio_config', methods=['POST'])
    def audio_config():
        """Configurar la calidad de audio."""
        data = request.json
        bitrate = data.get('bitrate')
        sampling_rate = data.get('sampling_rate')
        audio_channels = data.get('audio_channels')

        if bitrate is None or sampling_rate is None or audio_channels is None:
            return jsonify({"error": "Parámetros de audio incompletos (bitrate, sampling_rate, audio_channels)"}), 400

        if app.config['bot'] and hasattr(app.config['bot'], 'set_audio_quality'):
            success = app.config['bot'].set_audio_quality(
                bitrate=bitrate,
                sampling_rate=sampling_rate,
                audio_channels=audio_channels
            )
            if success:
                return jsonify({"success": True, "message": f"Configuración de audio aplicada: Bitrate {bitrate}kbps, SR {sampling_rate}Hz, Canales {audio_channels}"})
            else:
                return jsonify({"error": f"Valores de configuración de audio inválidos."}), 400
        else:
            logger.error("Bot no disponible o el método set_audio_quality no existe.")
            return jsonify({"error": "No se pudo configurar el audio en el bot."}), 500

    return app

def init_web(bot, host='0.0.0.0', port=5000):
    """Initializes and starts the Flask web server in a separate thread."""
    app = create_app(bot)
    
    def run_app():
        """Function to run the Flask app, used by the thread."""
        app.run(host=host, port=port, debug=False, use_reloader=False)
    
    web_thread = threading.Thread(target=run_app, daemon=True)
    web_thread.start()
    
    print(f"Servidor web iniciado en http://{host}:{port}")
    return web_thread