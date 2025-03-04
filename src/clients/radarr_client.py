import requests
from src.config import Config
from src.utils.logger import get_action_logger


class RadarrClient:
    def __init__(self, logger=get_action_logger("RadarrClient"), url=Config.RADARR_URL, api_key=Config.RADARR_API_KEY):
        self.url = url
        self.api_key = api_key
        self.headers = {"X-Api-Key": self.api_key}
        self.logger = logger

    def rescan_movie(self, movie_id):
        """Trigger a rescan of the movie in Radarr."""
        payload = {'name': 'RescanMovie', 'movieId': movie_id}
        response = requests.post(f'{self.url}/command', json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_all_movies(self):
        """
        Get a list of all movies in Radarr, including alternative titles.
        Returns a dictionary with all possible titles (main and alternatives) for each movie.
        """
        self.logger.info("Fetching all movies from Radarr...")

        try:
            response = requests.get(f'{self.url}/movie', headers=self.headers)
            response.raise_for_status()
            movies = response.json()
            self.logger.info(f"Successfully fetched {len(movies)} movies from Radarr.")
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Failed to fetch movies from Radarr: {str(e)}")
            return {}

        all_titles = {}
        alt_title_count = 0

        for movie in movies:
            main_title = movie['title'].lower()
            all_titles[main_title] = movie
            self.logger.debug(f"Added main title: '{movie['title']}'")

            for alt_title in movie.get('alternativeTitles', []):
                alt_title_lower = alt_title['title'].lower()
                if alt_title_lower != main_title:
                    all_titles[alt_title_lower] = movie
                    alt_title_count += 1
                    self.logger.debug(f"Added alternative title for '{movie['title']}': '{alt_title['title']}'")

        self.logger.info(f"Processed {len(movies)} movies with {alt_title_count} alternative titles.")
        self.logger.info(f"Total unique titles (including alternatives): {len(all_titles)}")

        # Print out some sample entries for verification
        sample_size = min(5, len(all_titles))
        self.logger.info("Sample entries from all_titles:")
        for i, (title, movie) in enumerate(list(all_titles.items())[:sample_size]):
            self.logger.info(f"Sample {i + 1}: '{title}' -> Movie ID: {movie['id']}, Main Title: '{movie['title']}'")

        return all_titles

    def search(self, movie_name):
        """Search for a movie in Radarr by name."""
        response = requests.get(f'{self.url}/movie/lookup', params={'term': movie_name}, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_movie_path(self, movie_id):
        """Get the path of a movie in Radarr by its ID."""
        response = requests.get(f'{self.url}/movie/{movie_id}', headers=self.headers)
        response.raise_for_status()
        return response.json()['path']

    def add_movie(self, tmdb_id, quality_profile_id, root_folder_path):
        """Add a new movie to Radarr."""
        movie_info = self.search(f"tmdb:{tmdb_id}")[0]
        payload = {
            "tmdbId": tmdb_id,
            "title": movie_info['title'],
            "qualityProfileId": quality_profile_id,
            "rootFolderPath": root_folder_path,
            "monitored": True,
            "addOptions": {
                "searchForMovie": True
            }
        }
        response = requests.post(f'{self.url}/movie', json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_quality_profiles(self):
        """Get all quality profiles from Radarr."""
        response = requests.get(f'{self.url}/qualityprofile', headers=self.headers)
        response.raise_for_status()
        return response.json()

    def get_root_folders(self):
        """Get all root folders from Radarr."""
        response = requests.get(f'{self.url}/rootfolder', headers=self.headers)
        response.raise_for_status()
        return response.json()


# Example usage
if __name__ == "__main__":
    radarr = RadarrClient()

    # Get all movies
    movies = radarr.get_all_movies()
    print(f"Total movies: {len(movies)}")

    # Search for a movie
    search_results = radarr.search("Inception")
    print(f"Search results: {search_results}")

    # Get quality profiles
    profiles = radarr.get_quality_profiles()
    print(f"Quality profiles: {profiles}")

    # Get root folders
    # folders = radarr.get_root_folders()
    # print(f"Root folders: {folders}")

    # Add a movie (uncomment to use)
    # new_movie = radarr.add_movie(tmdb_id=27205, quality_profile_id=1, root_folder_path="/path/to/movies")
    # print(f"Added new movie: {new_movie}")