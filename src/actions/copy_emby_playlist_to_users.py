from src.clients.emby_client import EmbyClient
from src.config import Config
from src.services.playlist_service import PlaylistService
from src.utils.logger import get_action_logger
logger = get_action_logger("copy_emby_playlist_to_users")
#
# This is a simple example of copying a playlist to a target user
#

async def copy_playlists_to_users(source_emby):
    # Create an array of target usernames
    target_usernames = ["Alyssa", "Dalton", "Laura", "Zuko", "Azula","Brittany","Adam","Chris","Jason"]

    # Get all the playlists for the source user
    playlists = source_emby.get_playlists()

    # Iterate over each playlist
    for playlist in playlists:
        # Iterate over the target usernames
        for target_username in target_usernames:
            # Check if the target username is in the playlist name
            if target_username in playlist["Name"]:
                try:
                    # Create an instance of the Emby client for the target user
                    target_emby = EmbyClient(Config.EMBY_URL, target_username, '')

                    # Create an instance of the PlaylistService
                    playlist_service = PlaylistService(source_emby, target_emby)

                    # Copy the playlist to the target user
                    new_playlist = playlist_service.copy_playlist_by_usernames(Config.EMBY_USERNAME, target_username, playlist["Id"])
                    print(f"Playlist '{playlist['Name']}' copied successfully to user '{target_username}'. New playlist ID: {new_playlist['Id']}")
                except ValueError as e:
                    print(f"Error copying playlist '{playlist['Name']}' to user '{target_username}': {str(e)}")
