import os
import re
import requests
import spotipy
from fuzzywuzzy import fuzz
from spotipy import SpotifyOAuth, CacheFileHandler
from src.utils.logger import setup_logger
from src.utils.string_utils import StringUtils

logger = setup_logger()


class SpotifyClient:
    def __init__(self, client_id, client_secret, redirect_uri, scope, config_root="/app/config/"):
        # Authenticate with Spotify API
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope,
                cache_handler=CacheFileHandler(cache_path=os.path.join(config_root + ".spotipy_cache"))
            )
        )

    def match_artists(self, spotify_artists, emby_artists):
        """
        Match Spotify artists with Emby artists using fuzzy string matching.
        Returns the maximum artist similarity score found.
        """
        # print("MATCH ARTISTS")
        # print(spotify_artists)
        # print(emby_artists)

        max_artist_score = 0
        for spotify_artist in spotify_artists:
            spotify_artist_name = StringUtils.clean_string(spotify_artist)
            for emby_artist in emby_artists:
                emby_artist_name = StringUtils.clean_string(emby_artist)
                artist_score = fuzz.ratio(spotify_artist_name, emby_artist_name)
                max_artist_score = max(max_artist_score, artist_score)
        return max_artist_score

    def match_song(self, spotify_song, emby_song):
        """
        Match a Spotify song with an Emby song using fuzzy string matching.
        """
        # print(spotify_song)
        # print(emby_song)
        try:
            spotify_title = StringUtils.clean_string(spotify_song.get("name", "").lower())
            spotify_artists = [artist.get("name", "").lower() for artist in spotify_song["artists"]]

            emby_title = StringUtils.clean_string(emby_song.get("Name", "").lower())
            emby_artists = [artist.lower() for artist in emby_song.get("Artists", [])]

            spotify_title_no_parentheses = remove_parentheses(spotify_title)
            emby_title_no_parentheses = remove_parentheses(emby_title)

            spotify_title_cleaned = clean_title(spotify_title)
            emby_title_cleaned = clean_title(emby_title)


            # print("SPOTIFY TITLE NO PARENTHESES", spotify_title_no_parentheses)
            # print("EMBY TITLE NO PARENTHESES", emby_title_no_parentheses)

            title_ratio = max(
                fuzz.ratio(spotify_title, emby_title),
                fuzz.ratio(spotify_title_no_parentheses, emby_title_no_parentheses),
                fuzz.ratio(spotify_title_cleaned, emby_title_cleaned)
            )
            # print("TITLE RATIO", title_ratio)

            artist_ratio = self.match_artists(spotify_artists, emby_artists)

            # print("ARTIST RATIO", artist_ratio)

            # Adjust the thresholds as needed
            title_threshold = 85
            artist_threshold = 75
            combined_threshold = 165  # Sum of title and artist thresholds

            if title_ratio >= title_threshold and artist_ratio >= artist_threshold:
                combined_score = title_ratio + artist_ratio
                if combined_score >= combined_threshold:
                    # print(f"MATCH: {spotify_title} by {spotify_artists} vs {emby_title} by {emby_artists}")
                    return True
            return False
        except Exception as e:

            logger.error(f"Error matching song: {str(e)}")
            return False

    def get_playlist_tracks(self, playlist_id):
        results = self.sp.playlist_tracks(playlist_id)
        tracks = results["items"]
        while results["next"]:
            results = self.sp.next(results)
            tracks.extend(results["items"])
        return tracks

    def get_playlists(self):
        return self.sp.current_user_playlists()

    def get_spotify(self):
        return self.sp

    def get_playlist_image(self, playlist_id):
        results = self.sp.playlist_cover_image(playlist_id)
        if results:
            image_url = results[0]['url']
            response = requests.get(image_url)
            if response.status_code == 200:
                image_data = response.content
                return image_data
        return None


    def get_liked_songs(self):
        liked_songs = []
        results = self.sp.current_user_saved_tracks()
        while results:
            liked_songs.extend(results["items"])
            results = self.sp.next(results)
        return liked_songs

    def get_featured_playlists(self):
        return self.sp.featured_playlists()["playlists"]
        pass



    def get_categorys(self):
        return self.sp.categories(country="US")["categories"]

    def get_category_by_name(self, name):
        for category in self.sp.categories(country="US")["categories"]["items"]:
            logger.info(f"Checking category: {category['name']} == {name}")
            if category["name"].lower() == name.lower():
                logger.info(f"Found category: {category['name']}")
                return category
        return None

    def get_category_playlists_by_name(self, name):
        category = self.get_category_by_name(name)
        if category:
            logger.info(f"Getting playlists from category: {category['name']}")
            return self.sp.category_playlists(category["id"])["playlists"]
        return None


    def get_made_for_you(self):
        # get the category id for made for you
        playlists = self.get_category_playlists_by_name("Made for You")
        logger.info(f"Made for you playlists: {playlists}")

        # pretty print all the playlists
        # for playlist in playlists['items']:
        #     logger.debug(f"Playlist name: {playlist['name']}")
        #     logger.debug(f"Playlist description: {playlist['description']}")
        #     logger.debug(f"Playlist owner: {playlist['owner']['display_name']}")
        #     logger.debug(f"Playlist tracks: {playlist['tracks']['total']}")
        #     logger.debug(f"Playlist images: {playlist['images']}")
        #     logger.debug(f"Playlist collaborative: {playlist['collaborative']}")
        # get the tracks in the playlists
        return playlists


def remove_parentheses(text):
    if text:
        return re.sub(r'\([^)]*\)', '', text).strip()
    else:
        return text

def clean_title(title):
    # Convert to lowercase
    title = title.lower()

    # logging.info(f"Current title: {title}")

    # Remove text after featuring, feat, ft, etc.
    patterns = [
        r'\(feat\..*?\)',
        r'\(ft\..*?\)',
        r'\(featuring.*?\)',
        r'feat\..*',
        r'ft\..*',
        r'featuring.*',
        r'\(with.*?\)',
        r'\(prod\..*?\)',
        r'\(produced by.*?\)',
        r'- radio edit',
        r'- single version',
        r'- album version',
        r'\(remaster(ed)?\)',
        r'- remaster(ed)?',
        r'\(remix\)',
        r'- remix',
        r'\(live\)',
        r'- live',
        r'\(acoustic\)',
        r'- acoustic',
        r'\(deluxe\)',
        r'- deluxe',
        r'\(extended\)',
        r'- extended',
        r'\(original mix\)',
        r'- original mix',
        r'\(album version\)',
        r'- album version',
        r'\(explicit\)',
        r'- explicit',
        r'\(clean\)',
        r'- clean',
        r'\d{4} (remaster|version)',
        r'\d{4} digital (remaster|version)',
    ]

    for pattern in patterns:
        title = re.sub(pattern, '', title, flags=re.IGNORECASE)

    # Remove any remaining parentheses and their contents
    title = re.sub(r'\([^)]*\)', '', title)

    # Remove common filler words
    # filler_words = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'by']
    title_words = title.split()
    # title_words = [word for word in title_words if word.lower() not in filler_words]
    title = ' '.join(title_words)

    # Remove any extra whitespace
    title = ' '.join(title.split())

    # logging.info(f"Cleaned Title: {title}")
    return title.strip()
