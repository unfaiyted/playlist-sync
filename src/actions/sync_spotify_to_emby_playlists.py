import requests

from src.config import Config
from src.utils.string_utils import StringUtils
from src.clients.emby_client import EmbyClient
from src.clients.spotify_client import SpotifyClient, clean_title
from src.utils.logger import get_action_logger

import sqlite3

logger = get_action_logger("sync_spotify_to_emby_playlists")

def try_match_and_add(track_name, artist_name, emby_playlist, emby, spot):
    emby_search_results = emby.search_for_track(track_name, artist_name)

    if emby_search_results:
        for result in emby_search_results:
            emby_item_id = result["Id"]
            logger.debug(f'Matching {track_name} with {result["Name"]}')
            if spot.match_song({"name": track_name, "artists": [{"name": artist_name}]}, result):
                try:
                    logger.info(f'Found match: {track_name} by {artist_name} in Emby')
                    emby.add_item_to_playlist(emby_playlist['Id'], emby_item_id)
                    logger.info(f"Added '{track_name}' by {artist_name} to Emby playlist")
                    return True
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Error adding track to Emby playlist: {track_name}")
                    logger.warning(f"Error message: {str(e)}")
    return False


async def sync_spotify_playlists(spot, emby, config_root="/app/config/"):
    conn = sqlite3.connect(config_root + 'unmatched_songs.db')
    c = conn.cursor()
    # Create the table to store unmatched songs if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS unmatched_songs
                 (playlist_name TEXT, track_name TEXT, artist_name TEXT, album_name TEXT)''')

    playlists = spot.get_playlists()
    featured_playlists = spot.get_featured_playlists()
    # made_for_you = spot.get_made_for_you()

    # list of categories to get playlists from
    categories = ["Made for You", "Pop", "Country", "Fall", "Mood","Indie", "Charts", "Discover", "In the Car"]

    all_playlists = playlists["items"] + featured_playlists["items"]
    # get all the playlists from the categories
    for category in categories:
        logger.info(f"Getting playlists from category: {category}")
        category_playlists = spot.get_category_playlists_by_name(category)
        if category_playlists:
            all_playlists += category_playlists["items"]

    # print(json.dumps(featured_playlists, indent=4))

    # print(made_for_you)

    # all_playlists = playlists["items"] + featured_playlists["items"] #+ made_for_you["items"]

    # Iterate over each Spotify playlist
    for playlist in all_playlists:
        playlist_name = playlist["name"]
        playlist_id = playlist["id"]
        playlist_owner = playlist["owner"]["display_name"]
        logger.info(f"Processing Spotify playlist: {playlist_name} ({playlist_owner})")

        emby_playlist_name = f"{playlist_name} ({playlist_owner})"

        emby_playlist_search_results = emby.search(emby_playlist_name, 'Playlist')

        if emby_playlist_search_results:
            # Delete the existing playlist
            existing_playlist_id = emby_playlist_search_results[0]['Id']

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
                f"Created Emby playlist: {playlist_name} (ID: {emby_playlist['Id']})"
            )
            # Get the playlist image from Spotify
            playlist_image_data = spot.get_playlist_image(playlist_id)
            if playlist_image_data:
                try:
                    emby.upload_image_data(emby_playlist['Id'], playlist_image_data)
                    logger.info(f"Uploaded playlist cover image for '{playlist_name}'")
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Error uploading playlist cover image: {str(e)}")
            else:
                logger.warning(f"No playlist cover image found for '{playlist_name}'")


        except (requests.exceptions.RequestException, KeyError) as e:
            logger.error(f"Error creating Emby playlist: {playlist_name}")
            logger.error(f"Error message: {str(e)}")

        # Get the tracks in the Spotify playlist
        tracks = spot.get_playlist_tracks(playlist_id)

        logger.info(f"Processing {len(tracks)} tracks in Spotify playlist")
        # Iterate over each track in the Spotify playlist
        added_tracks = 0
        unmatched_tracks = []
        for track in tracks:

            # skil if track is not available
            if track["track"] is None:
                logger.warning(f"Track is not available: {track}")
                continue

            if track["track"]["name"] is None:
                logger.warning(f"Track name is None: {track}")
                continue

            track_name = track["track"]["name"]
            artist_name = track["track"]["artists"][0]["name"]
            album_name = track["track"]["album"]["name"]

            if album_name is None:
                album_name = "Unknown Album"

            if try_match_and_add(track_name, artist_name, emby_playlist, emby, spot):
                added_tracks += 1
                continue

            clean_track_name = clean_title(track_name)
            clean_artist_name = StringUtils.remove_special_characters(artist_name)
            if clean_track_name != track_name or clean_artist_name != artist_name:
                if try_match_and_add(clean_track_name, clean_artist_name, emby_playlist, emby, spot):
                    added_tracks += 1
                    continue

            logger.warning(f"No match found for '{track_name}' by {artist_name} in Emby / clean: {clean_track_name}")
            # logging.warning(f"Cleaned track name: {clean_track_name}")
            # logging.warning(f"Cleaned artist name: {clean_artist_name}")

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
    spot = SpotifyClient(Config.SPOTIFY_CLIENT_ID, Config.SPOTIFY_CLIENT_SECRET, Config.SPOTIFY_REDIRECT_URI,
                         Config.SPOTIFY_SCOPE)
    emby = EmbyClient(Config.EMBY_URL, Config.EMBY_USERNAME, Config.EMBY_PASSWORD)
    logger.info("Sync Spotify Playlist: Emby client initialized with URL: " + Config.EMBY_URL)
    sync_spotify_playlists(spot, emby)
