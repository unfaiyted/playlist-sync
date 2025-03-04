import requests
from src.config import Config
from src.utils.string_utils import StringUtils
from src.clients.emby_client import EmbyClient
from src.clients.spotify_client import SpotifyClient
from src.utils.logger import get_action_logger
import sqlite3

logger = get_action_logger("sync_spotify_liked")

def sync_spotify_liked(spot, emby, config_root="/app/config/"):
    # Connect to the SQLite database (it will be created if it doesn't exist)
    conn = sqlite3.connect(config_root + Config.DATABASE_FILE_NAME)
    c = conn.cursor()

    # Create the table to store unmatched songs if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS unmatched_songs
                 (playlist_name TEXT, track_name TEXT, artist_name TEXT, album_name TEXT)''')

    # Get the user's playlists from Spotify
    playlists = spot.get_playlists()
    # Iterate over each Spotify playlist
    playlist_name = "Favorites"
    playlist_id = "0"
    playlist_owner = "Dane"
    logger.info(f"Processing Spotify playlist: {playlist_name} ({playlist_owner})")

    emby_playlist_name = f"{playlist_name} ({playlist_owner})"

    emby_playlist_search_results = emby.search(emby_playlist_name, 'Playlist')

    if emby_playlist_search_results:
        # Delete the existing playlist
        existing_playlist_id = emby_playlist_search_results[0]["Id"]

        for existing_playlist in emby_playlist_search_results:
            if (
                    existing_playlist["Name"] == emby_playlist_name
                    and existing_playlist["Type"] == "Playlist"
            ):
                emby.delete_playlist(existing_playlist['Id'])
                logger.info(
                    f"Deleted existing Emby playlist: {emby_playlist_name} (ID: {existing_playlist_id})"
                )

    # Create a new playlist in Emby
    try:
        emby_playlist = emby.create_playlist(emby_playlist_name, 'Audio')
        logger.info(
            f"Created Emby playlist: {playlist_name} (ID: {emby_playlist["Id"]})"
        )
        # Get the playlist image from Spotify
        # playlist_image_data = spot.get_playlist_image(playlist_id)
        # if playlist_image_data:
        #     try:
        #         emby.upload_image_data(emby_playlist['Id'], playlist_image_data)
        #         logging.info(f"Uploaded playlist cover image for '{playlist_name}'")
        #     except requests.exceptions.RequestException as e:
        #         logging.warning(f"Error uploading playlist cover image: {str(e)}")
        # else:
        #     logging.warning(f"No playlist cover image found for '{playlist_name}'")
    except (requests.exceptions.RequestException, KeyError) as e:
        logger.error(f"Error creating Emby playlist: {playlist_name}")
        logger.error(f"Error message: {str(e)}")

    # Get the tracks in the Spotify playlist
    tracks = spot.get_liked_songs()

    logger.info(f"Processing {len(tracks)} tracks in Spotify playlist")
    # Iterate over each track in the Spotify playlist
    added_tracks = 0
    unmatched_tracks = []
    for track in tracks:
        track_name = track["track"]["name"]
        artist_name = track["track"]["artists"][0]["name"]
        album_name = track["track"]["album"]["name"]
        clean_track_name = StringUtils.remove_special_characters(track_name)
        clean_artist_name = StringUtils.remove_special_characters(artist_name)

        emby_search_results = emby.search_for_track(track_name, artist_name)
        emby_search_results_cleaned = emby.search_for_track(
            clean_track_name, clean_artist_name
        )

        if emby_search_results:
            found_match = False
            for result in emby_search_results:
                if found_match:
                    break

                emby_item_id = result["Id"]

                logger.debug(f'Matching {track["track"]["name"]} with {result["Name"]}')
                if spot.match_song(track["track"], result):
                    logger.debug(f"Matched track: {track_name}")
                    try:
                        emby.add_item_to_playlist(emby_playlist['Id'], emby_item_id)
                        logger.info(
                            f"Added '{track_name}' by {artist_name} to Emby playlist"
                        )
                        found_match = True
                        added_tracks += 1
                    except requests.exceptions.RequestException as e:
                        logger.warning(
                            f"Error adding track to Emby playlist: {track_name}"
                        )
                        logger.warning(f"Error message: {str(e)}")
                else:
                    logger.warning(
                        f"No match found for '{track_name}' by {artist_name} in Emby, failed match_song"
                    )
                    logger.warning(f"SPOTIFY: {track_name} by {artist_name}")
                    logger.warning(
                        f"EMBY: {result['Name']} by {result.get('Artists', [])}"
                    )
        else:
            logger.warning(
                f"No match found for '{track_name}' by {artist_name} in Emby"
            )
            unmatched_tracks.append((playlist_name, track_name, artist_name, album_name))

    # Insert the unmatched songs into the database
    c.executemany('INSERT INTO unmatched_songs VALUES (?, ?, ?, ?)', unmatched_tracks)
    conn.commit()

    # Calculate the match percentage for the current playlist
    if len(tracks) > 0:
        match_percentage = (added_tracks / len(tracks)) * 100
        logger.info(f"Match percentage for playlist '{playlist_name}': {match_percentage:.2f}%")

    added_tracks = 0

    # Close the database connection
    conn.close()


if __name__ == "__main__":
    # Get the user's playlists from Spotify
    spot = SpotifyClient(Config.SPOTIFY_CLIENT_ID, Config.SPOTIFY_CLIENT_SECRET, Config.SPOTIFY_REDIRECT_URI,
                         Config.SPOTIFY_SCOPE)
    emby = EmbyClient(Config.EMBY_URL, Config.EMBY_USERNAME, Config.EMBY_PASSWORD)

    sync_spotify_liked(spot, emby)
