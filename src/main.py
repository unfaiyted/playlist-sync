# codebase/emby-scripts/src/main.py
import asyncio

from src.actions.identify_music_with_missing_metadata import (
    match_metadata_unorg_music_folder,
)
from src.actions.move_org_movies_to_destination import move_organized_movies
from src.actions.move_org_music_to_destination import move_organized_music
from src.actions.move_org_spotify_songs_to_server import (
    move_org_spotify_music_to_server,
)
from src.actions.move_org_tv_to_destination import move_organized_tv
from src.actions.sort_downloaded_spotify_tracks import sort_downloaded_spotify_tracks
from src.clients.sonarr_client import SonarrClient
from src.config import Config
from src.clients.emby_client import EmbyClient
from src.clients.spotify_client import SpotifyClient
from src.actions.sync_spotify_to_emby_playlists import sync_spotify_playlists
from src.actions.find_unmatched_songs_with_spotdl import find_unmatched_songs
from src.actions.delete_duplicate_emby_playlists import delete_duplicate_playlists
from src.actions.copy_emby_playlist_to_users import copy_playlists_to_users
from src.actions.sort_downloaded_albums import organize_music
from src.actions.move_unorg_movies_to_org_movies import organize_movies
from src.actions.move_unorg_tv_to_org import organize_episodes
from src.utils.logger import get_action_logger
from dotenv import load_dotenv

logger = get_action_logger("main")

# Load environment variables from .env file
load_dotenv()


async def playlist_tasks(emby, spotify):
    # 1. Sync Spotify playlists
    logger.info("Starting Spotify playlist sync...")
    await sync_spotify_playlists(spotify, emby)
    logger.info("Spotify playlist sync completed.")

    # 2. Find unmatched songs
    logger.info("Finding unmatched songs...")
    await find_unmatched_songs(Config.MUSIC_SPOTIFY_DOWNLOAD_DIR)
    logger.info("Unmatched songs search completed.")

    # 3. organize spotify music
    logger.info("Organizing Spotify music...")
    await sort_downloaded_spotify_tracks(
        Config.MUSIC_SPOTIFY_DOWNLOAD_DIR, Config.MUSIC_SPOTIFY_ORGANIZED_DIR
    )
    logger.info("Spotify music organized.")

    # 3. Move org spotify music to server
    logger.info("Moving org spotify music to server...")
    await move_org_spotify_music_to_server(
        Config.MUSIC_SPOTIFY_ORGANIZED_DIR, Config.MUSIC_STORAGE_DIR, False
    )
    logger.info("Org spotify music moved to server.")

    # 3. Sync Spotify playlists again
    logger.info("Starting second Spotify playlist sync...")
    await sync_spotify_playlists(spotify, emby)
    logger.info("Second Spotify playlist sync completed.")

    # 4. Delete duplicate playlists
    logger.info("Deleting duplicate playlists...")
    delete_duplicate_playlists(emby)
    logger.info("Duplicate playlists deletion completed.")

    # 5. Copy playlists to other users
    logger.info("Copying playlists to other users...")
    await copy_playlists_to_users(emby)
    logger.info("Playlist copying completed.")


async def movie_organization_task():
    logger.info("Starting movie organization...")
    await organize_movies(
        Config.MOVIES_DOWNLOAD_DIR, Config.MOVIES_ORGANIZED_DIR, dry_run=False
    )
    logger.info("Movie organization completed.")
    await move_organized_movies(
        Config.MOVIES_ORGANIZED_DIR, Config.MOVIES_DOWNLOAD_DIR, dry_run=False
    )
    logger.info("Movies moved to server.")


async def tv_organization_task(sonarr):
    logger.info("Starting TV show organization...")
    await organize_episodes(
        Config.TV_DOWNLOAD_DIR, Config.TV_ORGANIZED_DIR, dry_run=False
    )
    logger.info("TV show organization completed.")
    await move_organized_tv(sonarr, Config.TV_ORGANIZED_DIR, dry_run=False)
    logger.info("TV shows moved to server.")


async def music_organization_task():
    logger.info("Getting music metadata...")
    await match_metadata_unorg_music_folder(Config.MUSIC_DOWNLOAD_DIR)
    logger.info("Music metadata retrieved.")
    logger.info("Starting music organization...")
    await organize_music(
        Config.MUSIC_DOWNLOAD_DIR, Config.MUSIC_ORGANIZED_DIR, dry_run=False
    )
    logger.info("Music organization completed.")
    logger.info("Moving organized music to destination...")
    await move_organized_music(
        Config.MUSIC_ORGANIZED_DIR, Config.MUSIC_STORAGE_DIR, dry_run=False
    )
    logger.info("Music moved to server.")


async def main():
    # Initialize clients
    emby = EmbyClient(Config.EMBY_URL, Config.EMBY_USERNAME, Config.EMBY_PASSWORD)
    logger.info("Emby client initialized with URL: " + Config.EMBY_URL)
    spotify = SpotifyClient(
        Config.SPOTIFY_CLIENT_ID,
        Config.SPOTIFY_CLIENT_SECRET,
        Config.SPOTIFY_REDIRECT_URI,
        Config.SPOTIFY_SCOPE,
    )
    logger.info(
        "Spotify client initialized with client ID: " + Config.SPOTIFY_CLIENT_ID
    )
    sonarr = SonarrClient(url=Config.SONARR_URL, api_key=Config.SONARR_API_KEY)
    logger.info("Sonarr client initialized with URL: " + Config.SONARR_URL)

    # Run all tasks concurrently
    await asyncio.gather(
        playlist_tasks(emby, spotify),
        # movie_organization_task(),
        # tv_organization_task(sonarr),
        music_organization_task(),
    )


if __name__ == "__main__":
    asyncio.run(main())
