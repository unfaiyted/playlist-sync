# codebase/emby-scripts/src/clients/navidrome_client.py

import requests
import hashlib
import time
import random
import string
from urllib.parse import urlencode
import logging
from fuzzywuzzy import fuzz
from src.utils.string_utils import StringUtils


class NavidromeClient:
    def __init__(self, base_url, username, password):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.salt = self.generate_salt()
        self.logger = logging.getLogger(__name__)

    def generate_salt(self, length=6):
        return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

    def get_auth_params(self):
        t = int(time.time() * 1000)
        token = hashlib.md5(f"{self.password}{self.salt}".encode()).hexdigest()
        return {
            'u': self.username,
            't': token,
            's': self.salt,
            'v': '1.16.1',
            'c': 'myapp',
            'f': 'json'
        }

    def make_request(self, endpoint, params=None):
        url = f"{self.base_url}/rest/{endpoint}"
        auth_params = self.get_auth_params()
        if params:
            auth_params.update(params)
        response = requests.get(url, params=auth_params)
        response.raise_for_status()
        return response.json()

    def get_playlists(self):
        response = self.make_request('getPlaylists')
        return response.get('subsonic-response', {}).get('playlists', {}).get('playlist', [])

    def get_playlist_by_name(self, name):
        playlists = self.get_playlists()
        return next((pl for pl in playlists if pl['name'] == name), None)

    def create_playlist(self, name):
        response = self.make_request('createPlaylist', {'name': name})
        return response.get('subsonic-response', {}).get('playlist')

    def clear_playlist(self, playlist_id):
        self.make_request('updatePlaylist', {'playlistId': playlist_id, 'songIdToRemove': ''})

    def search_track(self, title, artist):
        response = self.make_request('search3', {'query': f"{title} {artist}"})
        songs = response.get('subsonic-response', {}).get('searchResult3', {}).get('song', [])

        best_match = None
        best_score = 0
        for song in songs:
            title_score = fuzz.ratio(StringUtils.clean_string(title), StringUtils.clean_string(song['title']))
            artist_score = fuzz.ratio(StringUtils.clean_string(artist), StringUtils.clean_string(song['artist']))
            avg_score = (title_score + artist_score) / 2
            if avg_score > best_score:
                best_score = avg_score
                best_match = song

        return best_match if best_score > 80 else None

    def add_track_to_playlist(self, playlist_id, track_id):
        self.make_request('updatePlaylist', {'playlistId': playlist_id, 'songIdToAdd': track_id})

    def match_song(self, spotify_track, navidrome_track):
        spotify_title = StringUtils.clean_string(spotify_track.get("name", "").lower())
        spotify_artist = StringUtils.clean_string(spotify_track.get("artist", "").lower())

        navidrome_title = StringUtils.clean_string(navidrome_track.get("title", "").lower())
        navidrome_artist = StringUtils.clean_string(navidrome_track.get("artist", "").lower())

        title_ratio = fuzz.ratio(spotify_title, navidrome_title)
        artist_ratio = fuzz.ratio(spotify_artist, navidrome_artist)

        # Adjust these thresholds as needed
        return title_ratio > 80 and artist_ratio > 80