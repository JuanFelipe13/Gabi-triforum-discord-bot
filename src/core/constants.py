"""Core constants used throughout the application."""
import re

URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://' 
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|' 
    r'localhost|' 
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' 
    r'(?::\d+)?'  
    r'(?:/?|[/?]\S+)$', re.IGNORECASE
)
"""Regular expression for matching URLs."""

# Path to the cookies file. Update this with the actual path on your server.
# Example: '/path/to/your/cookies.txt'
# Set to None if you are not using a cookies file.
YTDLP_COOKIES_FILE = '/home/ec2-user/Gabi-triforum-discord-bot/cookies.txt'
"""Path to the cookies file for yt-dlp authentication."""

YTDLP_SEARCH_OPTIONS = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'extract_flat': 'in_playlist',
    'skip_download': True,
    'force_generic_extractor': True,
    'ignoreerrors': True,
    'nocheckcertificate': True,
    'logtostderr': False,
    'no_color': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'cachedir': '.yt-dlp-cache'
}
"""Options dictionary for yt-dlp when performing searches."""

YTDLP_OPTIONS_PLAYLIST_INFO = {
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
    'cachedir': '.yt-dlp-cache',
    'socket_timeout': 10,
    'retries': 3,
    'fragment_retries': 3,
    'http_chunk_size': 5242880,
    'external_downloader_args': ['-timeout', '10'],
    'youtube_include_dash_manifest': False,
    'prefer_insecure': True,
    'legacy_server_connect': True,
    'live_from_start': True,
    'live_buffer_size': 32768,
    'cookies': YTDLP_COOKIES_FILE if YTDLP_COOKIES_FILE else None,
}
"""Options dictionary for yt-dlp when extracting basic playlist/song information quickly."""

YTDLP_OPTIONS_PLAYBACK = {
    'format': 'bestaudio/best',
    'quiet': True,
    'no_warnings': True,
    'skip_download': True,
    'force_generic_extractor': False,
    'ignoreerrors': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'logtostderr': False,
    'no_color': True,
    'source_address': '0.0.0.0',
    'cachedir': '.yt-dlp-cache',
    'socket_timeout': 10,
    'retries': 3,
    'fragment_retries': 3,
    'http_chunk_size': 5242880,
    'external_downloader_args': ['-timeout', '10'],
    'youtube_include_dash_manifest': False,
    'prefer_insecure': True,
    'legacy_server_connect': True,
    'live_from_start': True,
    'live_buffer_size': 32768,
    'cookies': YTDLP_COOKIES_FILE if YTDLP_COOKIES_FILE else None,
    'postprocessors': [{
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'opus',
        'preferredquality': '0',
    }]
}
"""Options dictionary for yt-dlp when extracting detailed audio/video information for playback."""

FFMPEG_OPTIONS_TEMPLATE = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -timeout 10000000 -nostdin -nostats -thread_queue_size 2048',
    'options': '-vn -b:a {bitrate}k -bufsize {bufsize}k -probesize 1M -analyzeduration 1M -ar {sampling_rate} -ac {audio_channels} -max_muxing_queue_size 2048'
}
"""Template for FFmpeg audio processing options. Bitrate will be formatted in.""" 