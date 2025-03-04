# codebase/emby-scripts/src/actions/sync_spotify_to_navidrome_playlists.py

import requests
from src.config import Config
from src.clients.spotify_client import SpotifyClient
from src.clients.navidrome_client import NavidromeClient
from src.utils.logger import get_action_logger
logger = get_action_logger('sync_spotify_to_navidrome_playlists')


def try_match_and_add(track_name, artist_name, navidrome_playlist, spotify, navidrome):
    spotify_track = {"name": track_name, "artist": artist_name}

    try:
        navidrome_track = navidrome.search_track(track_name, artist_name)
        if navidrome_track:
            if navidrome.match_song(spotify_track, navidrome_track):
                navidrome.add_track_to_playlist(navidrome_playlist['id'], navidrome_track['id'])
                logger.info(f"Added '{track_name}' by {artist_name} to Navidrome playlist")
                return True
            else:
                logger.warning(f"Found track but it didn't match closely enough: '{track_name}' by {artist_name}")
        else:
            logger.warning(f"No match found for '{track_name}' by {artist_name} in Navidrome")
    except requests.exceptions.RequestException as e:
        logger.warning(f"Error adding track to Navidrome playlist: {track_name}")
        logger.warning(f"Error message: {str(e)}")

    return False


def sync_navidrome_playlists(spotify, navidrome):
    spotify_playlists = spotify.get_playlists()

    for spotify_playlist in spotify_playlists['items']:
        playlist_name = spotify_playlist['name']
        playlist_id = spotify_playlist['id']
        logger.info(f"Processing Spotify playlist: {playlist_name}")

        # Check if playlist exists in Navidrome, create if not
        navidrome_playlist = navidrome.get_playlist_by_name(playlist_name)
        if not navidrome_playlist:
            navidrome_playlist = navidrome.create_playlist(playlist_name)
            logger.info(f"Created Navidrome playlist: {playlist_name}")
        else:
            # Clear existing tracks in Navidrome playlist
            navidrome.clear_playlist(navidrome_playlist['id'])
            logger.info(f"Cleared existing tracks in Navidrome playlist: {playlist_name}")

        # Get tracks from Spotify playlist
        spotify_tracks = spotify.get_playlist_tracks(playlist_id)

        added_tracks = 0
        for item in spotify_tracks:
            track = item['track']
            track_name = track['name']
            artist_name = track['artists'][0]['name']  # Assuming the first artist

            if try_match_and_add(track_name, artist_name, navidrome_playlist, spotify, navidrome):
                added_tracks += 1

        # Calculate the match percentage for the current playlist
        if len(spotify_tracks) > 0:
            match_percentage = (added_tracks / len(spotify_tracks)) * 100
            logger.info(f"Match percentage for playlist '{playlist_name}': {match_percentage:.2f}%")


if __name__ == "__main__":
    spotify = SpotifyClient(Config.SPOTIFY_CLIENT_ID, Config.SPOTIFY_CLIENT_SECRET, Config.SPOTIFY_REDIRECT_URI,
                            Config.SPOTIFY_SCOPE)
    navidrome = NavidromeClient(Config.NAVIDROME_URL, Config.NAVIDROME_USERNAME, Config.NAVIDROME_PASSWORD)

    sync_navidrome_playlists(spotify, navidrome)