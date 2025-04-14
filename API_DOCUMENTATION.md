# Documentación de la API del Music Bot

## Descripción
Esta documentación describe la API REST del Music Bot, que proporciona endpoints para gestionar listas de reproducción, buscar música y obtener información del clima.

## Acceso a la Documentación Swagger
La documentación interactiva de la API está disponible en:
```
http://127.0.0.1:8000/swagger
```

## Endpoints

### Status
- **GET /api/status**
  - Obtiene el estado actual del bot
  - Retorna información sobre la conexión, número de servidores y tiempo de actividad

### Playlists
- **GET /api/playlists**
  - Obtiene todas las listas de reproducción disponibles
  - Retorna un array con las playlists y sus canciones

- **POST /api/playlist/add**
  - Añade una canción a una playlist específica
  - Requiere el nombre de la playlist y la información de la canción

### Búsqueda
- **GET /api/search**
  - Busca canciones en YouTube
  - Requiere un parámetro de consulta 'q'
  - Retorna hasta 5 resultados con información detallada

### Clima
- **GET /api/weather**
  - Obtiene información meteorológica de una ciudad
  - Requiere el nombre de la ciudad como parámetro
  - Retorna datos detallados del clima actual

## Ejemplos de Uso

### Obtener Estado del Bot
```bash
curl http://127.0.0.1:8000/api/status
```

### Buscar Canciones
```bash
curl "http://127.0.0.1:8000/api/search?q=nombre%20de%20la%20canción"
```

### Añadir Canción a Playlist
```bash
curl -X POST http://127.0.0.1:8000/api/playlist/add \
  -H "Content-Type: application/json" \
  -d '{"playlist": "Mi Playlist", "song": {"title": "Canción", "url": "..."}}'
```

### Obtener Clima
```bash
curl "http://127.0.0.1:8000/api/weather?city=Madrid"
```

## Códigos de Respuesta
- 200: Solicitud exitosa
- 400: Solicitud inválida
- 404: Recurso no encontrado
- 500: Error interno del servidor

## Notas
- La API está disponible en `http://127.0.0.1:8000`
- Todas las respuestas están en formato JSON
- Para más detalles y pruebas interactivas, visite la interfaz Swagger UI 