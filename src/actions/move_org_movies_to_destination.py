import os
import re
import shutil
from src.utils.logger import get_action_logger
from src.utils.string_utils import StringUtils

logger = get_action_logger("move_org_movies_to_destination")

def get_existing_movies(destination_folder):
    existing_movies = {}
    for movie in os.listdir(destination_folder):
        title, year = StringUtils.get_movie_info(movie)
        if title and year:
            existing_movies[movie] = (StringUtils.clean_movie_name(title), year)
    return existing_movies

async def move_organized_movies(source_folder, destination_folder, dry_run=False):
    existing_movies = get_existing_movies(destination_folder)

    for movie_folder in os.listdir(source_folder):
        source_path = os.path.join(source_folder, movie_folder)
        if os.path.isdir(source_path):
            title, year = StringUtils.get_movie_info(movie_folder)
            if title and year:
                clean_title = StringUtils.clean_movie_name(title)
                new_folder_name = f"{clean_title} ({year})"
                destination_path = os.path.join(destination_folder, new_folder_name)

                # Check if similar movie exists
                similar_movie = None
                for existing_movie, (existing_title, existing_year) in existing_movies.items():
                    if StringUtils.is_similar_movie(clean_title, year, existing_title, existing_year):
                        similar_movie = existing_movie
                        break

                if similar_movie:
                    logger.warning(
                        f"Similar movie already exists: '{similar_movie}'. Skipping '{new_folder_name}' for manual review.")
                    continue

                if dry_run:
                    logger.info(f"[DRY RUN] Would move '{movie_folder}' to '{new_folder_name}'")
                else:
                    try:
                        shutil.move(source_path, destination_path)
                        logger.info(f"Moved '{movie_folder}' to '{new_folder_name}'")
                    except Exception as e:
                        logger.error(f"Error moving '{movie_folder}' to '{new_folder_name}': {e}")
            else:
                logger.warning(f"Folder '{movie_folder}' does not match expected format. Skipping.")


if __name__ == "__main__":
    # Usage example
    source_folder = r"\\192.168.0.101\download\downloads\ORG_Movies"
    destination_folder = r"\\192.168.0.110\raid\movies"

    dry_run = True  # Set to False to perform actual file operations

    print("Moving organized movies to final destination")
    move_organized_movies(source_folder, destination_folder, dry_run)
