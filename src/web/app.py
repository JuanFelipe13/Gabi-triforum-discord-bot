import os
import threading
import json
import requests
from flask import Flask, render_template, request, jsonify
import yt_dlp
from flasgger import Swagger
from ..core.constants import YTDLP_SEARCH_OPTIONS

def create_app(bot=None):
    app = Flask(__name__)
    app.config['bot'] = bot
    
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": 'apispec',
                "route": '/apispec.json',
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/swagger"
    }
    
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "Music Bot API",
            "description": "API para el bot de música de Discord",
            "version": "1.0.0"
        },
        "host": "127.0.0.1:8000",
        "basePath": "/",
        "schemes": ["http"]
    }
    
    Swagger(app, config=swagger_config, template=swagger_template)
    
    @app.route('/')
    def index():
        return render_template('index.html')
    
    @app.route('/weather')
    def weather_page():
        return render_template('weather.html')
    
    @app.route('/api/status')
    def status():
        """
        Obtener el estado del bot
        ---
        tags:
          - Status
        responses:
          200:
            description: Estado del bot
            schema:
              type: object
              properties:
                connected:
                  type: boolean
                guilds:
                  type: integer
                uptime:
                  type: string
          404:
            description: Bot no disponible
        """
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
        """
        Obtener todas las listas de reproducción
        ---
        tags:
          - Playlists
        responses:
          200:
            description: Lista de playlists
            schema:
              type: array
              items:
                type: object
          500:
            description: Error al cargar las playlists
        """
        playlist_path = 'playlists.json'
        if not os.path.exists(playlist_path):
            return jsonify([])
            
        try:
            with open(playlist_path, 'r', encoding='utf-8') as f:
                playlists_data = json.load(f)
            return jsonify(playlists_data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/search')
    def search():
        """
        Buscar canciones en YouTube
        ---
        tags:
          - Search
        parameters:
          - name: q
            in: query
            type: string
            required: true
            description: Término de búsqueda
        responses:
          200:
            description: Resultados de la búsqueda
            schema:
              type: array
              items:
                type: object
                properties:
                  title:
                    type: string
                  url:
                    type: string
                  webpage_url:
                    type: string
                  thumbnail:
                    type: string
                  duration:
                    type: integer
                  channel:
                    type: string
          400:
            description: Consulta vacía
          500:
            description: Error en la búsqueda
        """
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
        """
        Añadir una canción a una playlist
        ---
        tags:
          - Playlists
        parameters:
          - name: body
            in: body
            required: true
            schema:
              type: object
              required:
                - playlist
                - song
              properties:
                playlist:
                  type: string
                  description: Nombre de la playlist
                song:
                  type: object
                  description: Información de la canción
        responses:
          200:
            description: Canción añadida exitosamente
            schema:
              type: object
              properties:
                success:
                  type: boolean
                message:
                  type: string
          400:
            description: Datos inválidos
          500:
            description: Error al procesar la solicitud
        """
        playlist_path = 'playlists.json'
        data = request.json
        
        if not data:
            return jsonify({"error": "Datos no proporcionados"}), 400
            
        playlist_name = data.get('playlist')
        song = data.get('song')
        
        if not playlist_name or not song:
            return jsonify({"error": "Nombre de lista o canción no especificado"}), 400
        
        try:
            playlists = {}
            if os.path.exists(playlist_path):
                with open(playlist_path, 'r', encoding='utf-8') as f:
                    playlists = json.load(f)
            
            if playlist_name not in playlists:
                playlists[playlist_name] = []
            
            song_exists = False
            for existing_song in playlists[playlist_name]:
                if existing_song.get('title') == song.get('title'):
                    song_exists = True
                    break
            
            if not song_exists:
                playlists[playlist_name].append(song)
                
                with open(playlist_path, 'w', encoding='utf-8') as f:
                    json.dump(playlists, f, ensure_ascii=False, indent=2)
                
                return jsonify({"success": True, "message": f"Canción añadida a la lista {playlist_name}"})
            else:
                return jsonify({"success": False, "message": "La canción ya existe en la lista"})
                
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    @app.route('/api/weather')
    def weather():
        """
        Obtener información del clima
        ---
        tags:
          - Weather
        parameters:
          - name: city
            in: query
            type: string
            required: true
            description: Nombre de la ciudad
        responses:
          200:
            description: Información del clima
            schema:
              type: object
              properties:
                city:
                  type: string
                country:
                  type: string
                temperature:
                  type: number
                feels_like:
                  type: number
                humidity:
                  type: integer
                pressure:
                  type: integer
                description:
                  type: string
                icon:
                  type: string
                wind_speed:
                  type: number
                clouds:
                  type: integer
          400:
            description: Ciudad no especificada
          500:
            description: Error al obtener el clima
        """
        city = request.args.get('city', '')
        if not city:
            return jsonify({"error": "Ciudad no especificada"}), 400
        
        api_key = "4d8fb5b93d4af21d66a2948710284366"
        
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=es"
            response = requests.get(url)
            data = response.json()
            
            if response.status_code != 200:
                return jsonify({"error": data.get('message', 'Error en la API del clima')}), response.status_code
            
            weather_data = {
                "city": data['name'],
                "country": data['sys']['country'],
                "temperature": data['main']['temp'],
                "feels_like": data['main']['feels_like'],
                "humidity": data['main']['humidity'],
                "pressure": data['main']['pressure'],
                "description": data['weather'][0]['description'],
                "icon": data['weather'][0]['icon'],
                "wind_speed": data['wind']['speed'],
                "clouds": data['clouds']['all']
            }
            
            return jsonify(weather_data)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return app

def init_web(bot, host='127.0.0.1', port=5000):
    app = create_app(bot)
    
    def run_app():
        app.run(host=host, port=port, debug=False, use_reloader=False)
    
    web_thread = threading.Thread(target=run_app, daemon=True)
    web_thread.start()
    
    print(f"Servidor web iniciado en http://{host}:{port}")
    return web_thread 