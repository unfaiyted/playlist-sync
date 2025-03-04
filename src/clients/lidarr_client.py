import os

import requests
from fuzzywuzzy import fuzz

from src.config import Config
from src.main import logger
from src.utils.string_utils import StringUtils


class LidarrClient:
    def __init__(self, url=Config.LIDARR_URL, api_key=Config.LIDARR_API_KEY):
        self.url = url
        self.api_key = api_key
        self.headers = {"X-Api-Key": self.api_key}

    def get_artist(self, artist_name, add_if_not_matched=False):
        search_url = f"{self.url}/api/v1/artist/lookup"
        params = {"term": artist_name}

        try:
            response = requests.get(search_url, params=params, headers=self.headers)
            response.raise_for_status()
            search_results = response.json()

            if search_results:
                matched_artist = next(
                    (artist for artist in search_results if StringUtils.is_similar_artist(artist_name, artist['artistName'])),
                    None
                )
                if matched_artist:
                    # Check if the artist is already monitored in Lidarr
                    get_artist_url = f"{self.url}/api/v1/artist"
                    get_artist_response = requests.get(get_artist_url, headers=self.headers)
                    get_artist_response.raise_for_status()
                    existing_artists = get_artist_response.json()

                    existing_artist = next((artist for artist in existing_artists if
                                            artist['foreignArtistId'] == matched_artist['foreignArtistId']), None)

                    if existing_artist:
                        return existing_artist
                    else:
                        if add_if_not_matched:
                            # Add the artist to Lidarr
                            add_url = f"{self.url}/api/v1/artist"
                            add_data = {
                                "artistName": matched_artist['artistName'],
                                "foreignArtistId": matched_artist['foreignArtistId'],
                                "qualityProfileId": Config.LIDARR_QUALITY_PROFILE_ID,
                                "metadataProfileId": Config.LIDARR_METADATA_PROFILE_ID,
                                "monitored": True,
                                "monitorNewItems": Config.LIDARR_MONITOR_NEW_ITEMS,
                                "rootFolderPath": Config.MUSIC_STORAGE_DIR,
                                "addOptions": {
                                    "monitor": Config.LIDARR_MONITOR_OPTION,
                                    "searchForMissingAlbums": Config.LIDARR_SEARCH_FOR_MISSING_ALBUMS
                                },
                                "artistType": matched_artist.get('artistType', ''),
                                "path": os.path.join(Config.MUSIC_STORAGE_DIR, matched_artist['artistName']),
                                "mbId": matched_artist.get('mbId'),
                                "tags": [],
                                "genres": matched_artist.get('genres', []),
                                "status": matched_artist.get('status', 'continuing')
                            }
                            add_response = requests.post(add_url, json=add_data, headers=self.headers)
                            add_response.raise_for_status()
                            return add_response.json()
                        else:
                            return None

        except requests.RequestException as e:
            logger.error(f"Error communicating with Lidarr API: {str(e)}")

        return None

    def get_artists(self):
        """Fetch all artists from Lidarr."""
        url = f"{Config.LIDARR_URL}/api/v1/artist"

        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()  # Raise an exception for bad status codes
            artists = response.json()

            # Extract artist names from the response
            artist_names = [artist['artistName'] for artist in artists]

            logger.info(f"Successfully fetched {len(artist_names)} artists from Lidarr")
            return artist_names

        except requests.RequestException as e:
            logger.error(f"Failed to fetch artists from Lidarr: {str(e)}")
            return []

    def refresh_artist(self, artist_name):
        # Search for the artist in Lidarr
        try:
            artist = self.get_artist(artist_name, add_if_not_matched=True)
            if artist:
                logger.info(f"Artist '{artist_name}' found in Lidarr with ID: {artist['id']}")
                # Trigger a refresh for the artist
                refresh_url = f"{self.url}/api/v1/command"
                data = {
                    "name": "RefreshArtist",
                    "artistId": artist['id']
                }

                refresh_response = requests.post(refresh_url, json=data, headers=self.headers)
                refresh_response.raise_for_status()

                logger.info(f"Triggered refresh for artist '{artist_name}' in Lidarr with ID: {artist['id']}")
            else:
                logger.warning(f"Artist '{artist_name}' not found in Lidarr search results")
        except requests.RequestException as e:
            logger.error(f"Error communicating with Lidarr API: {str(e)}")
