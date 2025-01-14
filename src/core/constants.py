import re

URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://' 
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' 
    r'localhost|' 
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' 
    r'(?::\d+)?'  
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)

YTDLP_SEARCH_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'extract_flat': 'in_playlist',
    'skip_download': True,
    'force_generic_extractor': True,
    'ignoreerrors': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'logtostderr': False,
    'no_color': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'cachedir': False
}

YTDLP_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'extract_flat': 'in_playlist',
    'skip_download': True,
    'force_generic_extractor': False,
    'ignoreerrors': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'logtostderr': False,
    'no_color': True,
    'source_address': '0.0.0.0',
    'cachedir': False
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
} 