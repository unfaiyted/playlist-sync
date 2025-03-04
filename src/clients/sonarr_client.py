
import requests
from src.config import Config
from src.utils.logger import get_action_logger


class SonarrClient:
    def __init__(self, logger=get_action_logger("SonarrClient"), url=Config.SONARR_URL, api_key=Config.SONARR_API_KEY):
        self.url = url
        self.api_key = api_key
        self.headers = {"X-Api-Key": self.api_key}
        self.logger = logger

    def rescan_series(self, show_id):
        """Trigger a rescan of the series in Sonarr."""
        payload = {'name': 'RescanSeries', 'seriesId': show_id}
        response = requests.post(f'{self.url}/command', json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_all_shows(self):
        """
        Get a list of all TV shows in Sonarr, including alternative titles.
        Returns a dictionary with all possible titles (main and alternatives) for each show.
        """
        self.logger.info("Fetching all shows from Sonarr...")

        try:
            response = requests.get(f'{self.url}/series', headers=self.headers)
            response.raise_for_status()
            shows = response.json()
            self.logger.info(f"Successfully fetched {len(shows)} shows from Sonarr.")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch shows from Sonarr: {str(e)}")
            return {}

        all_titles = {}
        alt_title_count = 0

        for show in shows:
            main_title = show['title'].lower()
            all_titles[main_title] = show
            self.logger.debug(f"Added main title: '{show['title']}'")

            for alt_title in show.get('alternateTitles', []):
                alt_title_lower = alt_title['title'].lower()
                if alt_title_lower != main_title:
                    all_titles[alt_title_lower] = show
                    alt_title_count += 1
                    self.logger.debug(f"Added alternative title for '{show['title']}': '{alt_title['title']}'")

        self.logger.info(f"Processed {len(shows)} shows with {alt_title_count} alternative titles.")
        self.logger.info(f"Total unique titles (including alternatives): {len(all_titles)}")

        # Print out some sample entries for verification
        sample_size = min(5, len(all_titles))
        self.logger.info("Sample entries from all_titles:")
        for i, (title, show) in enumerate(list(all_titles.items())[:sample_size]):
            self.logger.info(f"Sample {i + 1}: '{title}' -> Show ID: {show['id']}, Main Title: '{show['title']}'")

        return all_titles

    def search(self, show_name):
        """Search for a TV show in Sonarr by name."""
        response = requests.get(f'{self.url}/series/lookup', params={'term': show_name},
                                headers={'X-Api-Key': self.api_key})
        response.raise_for_status()
        return response.json()

    def get_show_path(self, show_id):
        """Get the path of a TV show in Sonarr by its ID."""
        response = requests.get(f'{self.url}/series/{show_id}', headers={'X-Api-Key': self.api_key})
        response.raise_for_status()
        return response.json()['path']
