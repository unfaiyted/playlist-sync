from src.clients.emby_client import EmbyClient

class PlaylistService:
    def __init__(self, source_emby: EmbyClient, target_emby: EmbyClient):
        self.emby = source_emby
        self.target_emby = target_emby

    def copy_playlist(self, source_user_id: int , target_user_id: int, playlist_id: str):
        # Get the playlist details
        playlist = self.emby.get_list(playlist_id)

        print(f"Copying playlist {playlist_id} to {target_user_id}")
        # print(playlist)

        # Create a new playlist for the target user
        new_playlist = self.target_emby.create_playlist(playlist["Name"], playlist["Type"], user_id=target_user_id)

        # Get the items from the source playlist
        playlist_items, _ = self.emby.get_list_items(playlist_id)

        # Add the items to the new playlist
        for item in playlist_items:
            self.target_emby.add_item_to_playlist(new_playlist["Id"], item["Id"])

        return new_playlist

    def copy_playlist_by_usernames(self, source_username: str, target_username: str, playlist_id: str):

        source_user = self.emby.get_user_by_username(source_username)
        target_user = self.target_emby.get_user_by_username(target_username)

        if source_user is None:
            raise ValueError(f"Source user '{source_username}' not found.")
        if target_user is None:
            raise ValueError(f"Target user '{target_username}' not found.")

        # Call the copy_playlist method with the user IDs
        return self.copy_playlist(source_user['Id'], target_user["Id"], playlist_id)