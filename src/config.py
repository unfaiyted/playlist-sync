# config.py
import platform
import yaml
import os


# Get the directory of the current script
current_dir = os.path.dirname(os.path.abspath(__file__))

# Construct the path to settings.yml (assuming it's in the parent directory)
settings_path = os.path.join(current_dir, '..', 'config', 'settings.yml')

# Load the YAML file
with open(settings_path, 'r') as file:
    settings = yaml.safe_load(file)

if platform.system() == 'Windows':
    config_dir = 'C:/Users/Dane Miller/codebase/emby-scripts/config/'
else:
    config_dir = '/app/config/'

class Config:
    LIDARR_SEARCH_FOR_MISSING_ALBUMS = settings['lidarr']['search_for_missing_albums']
    LIDARR_MONITOR_OPTION = settings['lidarr']['monitor_option']
    LIDARR_MONITOR_NEW_ITEMS = settings['lidarr']['monitor_new_items']
    LIDARR_QUALITY_PROFILE_ID = settings['lidarr']['quality_profile_id']
    LIDARR_METADATA_PROFILE_ID = settings['lidarr']['metadata_profile_id']
    DRY_RUN = settings.get('dry_run', False)

    # Spotify API credentials
    SPOTIFY_CLIENT_ID = settings['spotify']['client_id']
    SPOTIFY_CLIENT_SECRET = settings['spotify']['client_secret']
    SPOTIFY_REDIRECT_URI = settings['spotify']['redirect_uri']
    SPOTIFY_SCOPE = settings['spotify']['scope']

    # Emby API credentials
    EMBY_URL = settings['emby']['url']
    EMBY_API_KEY = settings['emby']['api_key']
    EMBY_USER_ID = settings['emby']['user_id']
    EMBY_USERNAME = settings['emby']['username']
    EMBY_PASSWORD = settings['emby']['password']
    EMBY_CLIENT = settings['emby']['client']
    EMBY_DEVICE = settings['emby']['device']
    EMBY_DEVICE_ID = settings['emby']['device_id']
    EMBY_VERSION = settings['emby']['version']

    # Sonarr settings
    SONARR_API_KEY = settings['sonarr']['api_key']
    SONARR_URL = settings['sonarr']['url']
    SONARR_MATCH_THRESHOLD = settings['sonarr']['match_threshold']

    # Radarr settings
    RADARR_API_KEY = settings['radarr']['api_key']
    RADARR_URL = settings['radarr']['url']
    RADARR_MATCH_THRESHOLD = settings['radarr']['match_threshold']

    LIDARR_API_KEY = settings['lidarr']['api_key']
    LIDARR_URL = settings['lidarr']['url']
    LIDARR_MATCH_THRESHOLD = settings['lidarr']['match_threshold']

    # Navidrome settings
    NAVIDROME_URL = settings['navidrome']['url']
    NAVIDROME_USERNAME = settings['navidrome']['username']
    NAVIDROME_PASSWORD = settings['navidrome']['password']

    # Genius settings
    GENIUS_CLIENT_ID = settings['genius']['client_id']
    GENIUS_CLIENT_SECRET = settings['genius']['client_secret']
    GENIUS_ACCESS_TOKEN = settings['genius']['access_token']

    MUSIC_SPOTIFY_DOWNLOAD_DIR = settings['music']['spotify_download_dir']
    MUSIC_SPOTIFY_ORGANIZED_DIR = settings['music']['spotify_organized_dir']

    MUSIC_DOWNLOAD_DIR = settings['music']['download_dir']
    MUSIC_ORGANIZED_DIR = settings['music']['organized_dir']

    MUSIC_STORAGE_DIR = settings['music']['storage_dir']

    MOVIES_DOWNLOAD_DIR = settings['movies']['download_dir']
    MOVIES_ORGANIZED_DIR = settings['movies']['organized_dir']

    MOVIES_STORAGE_DIR = settings['movies']['storage_dir']

    TV_DOWNLOAD_DIR = settings['tv']['download_dir']
    TV_ORGANIZED_DIR = settings['tv']['organized_dir']

    TV_STORAGE_DIR = settings['tv']['storage_dir']

    DATABASE_FILE_NAME = 'unmatched_songs.db'
    DATABASE_FILE_PATH = os.path.join(config_dir, DATABASE_FILE_NAME)

    # if windows use one config dir if linux use another

    CONFIG_DIR = config_dir
