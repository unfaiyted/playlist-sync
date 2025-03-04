# codebase/emby-scripts/src/actions/delete_duplicate_emby_playlists.py

from src.config import Config
from src.clients.emby_client import EmbyClient
from src.utils.logger import get_action_logger

logger = get_action_logger("delete_duplicate_emby_playlists")

# Configure logging


def delete_duplicate_playlists(emby):
    # Initialize EmbyClient

    # Get all playlists from Emby
    all_playlists = emby.get_playlists()

    # Dictionary to store playlists by name
    playlists_by_name = {}

    for playlist in all_playlists:
        playlist_name = playlist['Name']
        playlist_id = playlist['Id']
        playlist_item_count = playlist.get('ChildCount', 0)

        if playlist_name in playlists_by_name:
            existing_playlist = playlists_by_name[playlist_name]
            existing_item_count = existing_playlist.get('ChildCount', 0)

            if playlist_item_count > existing_item_count:
                # Delete the existing playlist with fewer items
                emby.delete_playlist(existing_playlist['Id'])
                logger.info(f"Deleted duplicate playlist: {existing_playlist['Name']} (ID: {existing_playlist['Id']}) with {existing_item_count} items")
                playlists_by_name[playlist_name] = playlist
            else:
                # Delete the current playlist with fewer items
                emby.delete_playlist(playlist_id)
                logger.info(f"Deleted duplicate playlist: {playlist_name} (ID: {playlist_id}) with {playlist_item_count} items")
        else:
            playlists_by_name[playlist_name] = playlist

    logger.info("Finished deleting duplicate playlists")

if __name__ == "__main__":
    emby = EmbyClient(Config.EMBY_URL, Config.EMBY_USERNAME, Config.EMBY_PASSWORD)
    delete_duplicate_playlists(emby)