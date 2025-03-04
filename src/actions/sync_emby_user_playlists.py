from src.clients.emby_client import EmbyClient
from src.services.playlist_service import PlaylistService
from src.config import Config

def copy_playlists_to_users(source_emby, target_usernames, target_kids_usernames):
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

                    # Check if the playlist already exists for the target user
                    existing_playlist = next((p for p in target_emby.get_playlists() if p["Name"] == playlist["Name"]), None)

                    if existing_playlist:
                        # Delete the existing playlist
                        target_emby.delete_playlist(existing_playlist["Id"])
                        print(f"Existing playlist '{playlist['Name']}' deleted for user '{target_username}'.")

                    # Copy the playlist to the target user
                    new_playlist = playlist_service.copy_playlist_by_usernames(Config.EMBY_USERNAME, target_username, playlist["Id"])
                    print(f"Playlist '{playlist['Name']}' copied successfully to user '{target_username}'. New playlist ID: {new_playlist['Id']}")
                except ValueError as e:
                    print(f"Error copying playlist '{playlist['Name']}' to user '{target_username}': {str(e)}")

            # Check if the playlist has the tag 'Kids'
    for playlist in kids_playlists:
                # Iterate over the target kids usernames
                for target_username in target_kids_usernames:
                    try:
                        # Create an instance of the Emby client for the target user
                        target_emby = EmbyClient(Config.EMBY_URL, target_username, '')
                        # Create an instance of the PlaylistService
                        playlist_service = PlaylistService(source_emby, target_emby)

                        # Check if the playlist already exists for the target user
                        existing_playlist = next((p for p in target_emby.get_playlists() if p["Name"] == playlist["Name"]), None)

                        if existing_playlist:
                            # Delete the existing playlist
                            target_emby.delete_playlist(existing_playlist["Id"])
                            print(f"Existing playlist '{playlist['Name']}' deleted for user '{target_username}'.")

                        # Copy the playlist to the target user
                        new_playlist = playlist_service.copy_playlist_by_usernames(Config.EMBY_USERNAME, target_username, playlist["Id"])
                        print(f"Kids playlist '{playlist['Name']}' copied successfully to user '{target_username}'. New playlist ID: {new_playlist['Id']}")
                    except ValueError as e:
                        print(f"Error copying kids playlist '{playlist['Name']}' to user '{target_username}': {str(e)}")

if __name__ == "__main__":

    # Create an instance of the Emby client for the source user
    source_emby = EmbyClient(Config.EMBY_URL, Config.EMBY_USERNAME, Config.EMBY_PASSWORD)

    # Create an array of target usernames
    target_usernames = ["Alyssa", "Dalton", "Laura", "Zuko", "Azula","Chris"]
    target_kids_usernames = ["Alyssa", "Azula", "Zuko"]

    # Get all the playlists for the source user
    playlists = source_emby.get_playlists()
    kids_playlists = source_emby.get_tagged_playlist('Kids')

    copy_playlists_to_users(source_emby, target_usernames, target_kids_usernames)
