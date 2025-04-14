# TriForum Bot

Un bot de Discord multifuncional que integra múltiples APIs para proporcionar servicios de música, información meteorológica y procesamiento de contenido multimedia.

## Características principales

- **Reproducción de música**: Busca y reproduce música desde YouTube en canales de voz de Discord
- **Gestión de listas de reproducción**: Crea y gestiona listas de reproducción personalizadas
- **Información meteorológica**: Consulta el clima actual de cualquier ciudad
- **Procesamiento de contenido de Twitter**: Extrae y reproduce contenido multimedia desde Twitter/X

## APIs Integradas

Este proyecto integra las siguientes APIs:

1. **Discord API** (a través de discord.py)
   - Gestión de mensajes y comandos
   - Interacción con canales de voz
   - Permisos y roles de servidores

2. **YouTube API** (a través de yt-dlp)
   - Búsqueda de contenido
   - Extracción de información de videos
   - Streaming de audio en tiempo real

3. **Twitter API**
   - Procesamiento de enlaces y contenido de Twitter/X
   - Extracción de videos y contenido multimedia
   - Compatibilidad con múltiples dominios (twitter.com, x.com, fxtwitter.com)

4. **OpenWeatherMap API**
   - Información meteorológica en tiempo real
   - Datos de temperatura, humedad, viento, etc.
   - Cobertura mundial de ciudades

## Instalación

1. Clona este repositorio:
```bash
git clone https://github.com/yourusername/Ai-voice-chatbot-for-triforum.git
cd Ai-voice-chatbot-for-triforum
```

2. Instala las dependencias:
```bash
pip install -r requirements.txt
```

3. Instala FFmpeg (necesario para la reproducción de audio):
   - Windows: Descarga desde [ffmpeg.org](https://ffmpeg.org/download.html) y añade al PATH
   - Linux: `sudo apt-get install ffmpeg`
   - macOS: `brew install ffmpeg`

4. Configura las credenciales:
   - Crea un archivo `.env` en la raíz del proyecto
   - Añade tu token de Discord: `DISCORD_TOKEN=tu_token_aquí`

5. Inicia el bot:
```bash
python main.py
```

## Interfaz Web

El proyecto incluye una interfaz web simple que permite:
- Ver el estado del bot
- Buscar música en YouTube
- Ver las listas de reproducción
- Consultar información meteorológica

Para acceder a la interfaz web, abre un navegador y visita:
```
http://localhost:5000
```

## Uso del Bot en Discord

El bot responde a los siguientes comandos (prefijo predeterminado: `!`):

- `!play <canción o URL>`: Reproduce una canción
- `!pause`: Pausa la reproducción actual
- `!resume`: Reanuda la reproducción
- `!skip`: Salta a la siguiente canción
- `!queue`: Muestra la cola de reproducción
- `!playlist create <nombre>`: Crea una nueva lista de reproducción
- `!playlist add <nombre> <canción>`: Añade una canción a una lista
- `!playlist play <nombre>`: Reproduce una lista completa

## Requisitos

- Python 3.8 o superior
- FFmpeg
- Conexión a Internet
- Token de bot de Discord

## Contribuir

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:

1. Haz fork del repositorio
2. Crea una rama para tu función (`git checkout -b feature/amazing-feature`)
3. Haz commit de tus cambios (`git commit -m 'Add some amazing feature'`)
4. Haz push a la rama (`git push origin feature/amazing-feature`)
5. Abre un Pull Request

## Licencia

Este proyecto está licenciado bajo la Licencia MIT - consulta el archivo LICENSE para más detalles.

## Créditos

Desarrollado como parte de un proyecto académico para demostrar la integración de múltiples APIs en una aplicación funcional. 