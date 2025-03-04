import re

from fuzzywuzzy import fuzz


class StringUtils:

    @staticmethod
    def clean_string(s):
        """
        Helper function to remove non-alphanumeric characters and convert to lowercase.
        """
        return re.sub(r"[^a-zA-Z0-9\s]", "", s).lower()

    @staticmethod
    def remove_special_characters(text):
        # Remove special characters, brackets, parentheses, and their contents
        if text is None:
            return ""
        if not isinstance(text, str):
            text = str(text)

        cleaned_text = re.sub(r"[\[\]\(\)]*", "", text)
        cleaned_text = re.sub(r"[^a-zA-Z0-9\s]", "", cleaned_text)
        # cleaned_text = re.sub(r'[<>:"/\\|?*]', "_", cleaned_text)
        cleaned_text = cleaned_text.rstrip('. ')

        return cleaned_text.strip()

    # def sanitize_filename(filename):
    #     # Replace problematic characters with underscores
    #     # sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
    #     # Remove trailing dots and spaces
    #     # sanitized = sanitized.rstrip('. ')
    #     # Ensure the filename isn't empty after sanitization
    #     return sanitized or "Unknown"

    @staticmethod
    def extract_year(name):
        """Extract a 4-digit year from a string if present."""
        import re
        match = re.search(r'\b(19\d{2}|20\d{2})\b', name)
        return int(match.group(1)) if match else None

    @staticmethod
    def is_similar_artist(new_artist, existing_artist, threshold=90):
        # remove 'the' from the beginning of the artist name
        new_artist = new_artist.replace('the ', '', 1)
        existing_artist = existing_artist.replace('the ', '', 1)

        return fuzz.ratio(new_artist.lower(), existing_artist.lower()) >= threshold

    @staticmethod
    def is_similar_movie(new_title, new_year, existing_title, existing_year, title_threshold=95):
        return (new_year == existing_year) and (
                    fuzz.ratio(new_title.lower(), existing_title.lower()) >= title_threshold)

    @staticmethod
    def get_episode_info(filename):
        """Extract season and episode numbers from filename."""
        match = re.search(r'S(\d{2})E(\d{2})', filename, re.IGNORECASE)
        if match:
            return match.group(1), match.group(2)
        return None, None

    @staticmethod
    def get_movie_info(filename):
        """Extract movie title and year from filename."""
        match = re.search(r'(.+) \((\d{4})\)', filename)
        if match:
            return match.group(1), match.group(2)
        return None, None


    @staticmethod
    def clean_movie_name(name):
        # Remove resolution indicators
        name = re.sub(r'\b(1080p|720p|2160p|4k|Unrated)\b', '', name, flags=re.IGNORECASE)
        # Remove extra spaces and strip
        name = re.sub(r'\s+', ' ', name).strip()
        return name
