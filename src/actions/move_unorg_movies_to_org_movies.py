import os
import re
import shutil
from src.utils.logger import get_action_logger
logger = get_action_logger("move_unorg_movies_to_org_movies")


def clean_movie_name(name):
    # List of terms to remove

    remove_terms = [
        r'\d{3,4}p', 'uhd', 'remux', 'hevc', 'hdr', 'atmos', 'truehd',
        'bluray', 'brrip', 'bdrip', 'webdl', 'web-dl', 'webrip', 'dvdrip', 'hdrip',
        'x264', 'x265', 'xvid', 'divx', 'h264', 'h265',
        'aac', 'ac3', 'dts',
        'hdtv', 'sdtv', 'Xhin0',
        'proper', 'repack', 'extended', 'limited', 'unrated',
        'multi', 'dual', 'dubbed',
        'ita', 'eng', 'spa', 'fin', 'sub',
        '_unpack_'
    ]

    # Remove the terms
    for term in remove_terms:
        name = re.sub(rf'\b{term}\b', '', name, flags=re.IGNORECASE)

    # Remove any remaining dots, underscores, or extra spaces
    name = re.sub(r'[._]', ' ', name)
    name = re.sub(r'\s+', ' ', name).strip()

    return name


async def organize_movies(root_folder, destination_root, dry_run=False):
    movie_extensions = [".avi", ".mp4", ".mkv", ".mov", ".wmv"]

    for folder_name in os.listdir(root_folder):
        logger.info('Looking in ' + folder_name)
        folder_path = os.path.join(root_folder, folder_name)
        if os.path.isdir(folder_path):
            # Clean the folder name
            cleaned_name = clean_movie_name(folder_name)

            # Try to match movie name and year
            match = re.search(r'(.+?)(?:\s*[\(\[\{])?\s*(\d{4})(?:\s*[\)\]\}])?\s*', cleaned_name)

            if match:
                movie_name, year = match.groups()
                movie_name = movie_name.strip().title()

                # Create the new folder structure
                new_folder_name = f"{movie_name} ({year})"
                new_folder_path = os.path.join(destination_root, new_folder_name)

                logger.info(f'Found match: {new_folder_name}')

                if not dry_run:
                    os.makedirs(new_folder_path, exist_ok=True)

                for file_name in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file_name)
                    if os.path.isfile(file_path):
                        _, extension = os.path.splitext(file_name)
                        if extension.lower() in movie_extensions:
                            new_file_name = f"{movie_name} ({year}){extension}"
                            new_file_path = os.path.join(new_folder_path, new_file_name)

                            if os.path.exists(new_file_path):
                                existing_size = os.path.getsize(new_file_path)
                                new_size = os.path.getsize(file_path)

                                if new_size == existing_size:
                                    logger.info(f"File {file_name} already exists in {new_folder_path}")
                                    if not dry_run:
                                        os.remove(file_path)
                                        logger.info(f"Deleted {file_name}")
                                elif new_size < existing_size:
                                    logger.info(f"File {file_name} already exists in {new_folder_path} and is smaller than the original file")
                                    if not dry_run:
                                        os.remove(file_path)
                                else:
                                    logger.info(f"File {file_name} already exists in {new_folder_path} and is larger than the original file")
                                    if not dry_run:
                                        logger.info(f"Copying {file_name} to {new_file_path}")
                                        shutil.copy2(file_path, new_file_path)
                                        os.remove(file_path)
                                        logger.info(f"Deleted {file_name}")
                            else:
                                if dry_run:
                                    logger.info(f"[DRY RUN] Would copy {file_name} to {new_file_path}")
                                else:
                                    logger.info(f'Copying {file_name} to {new_file_path}')
                                    try:
                                        shutil.copy2(file_path, new_file_path)
                                        logger.info(f"Copied {file_name} to {new_file_path}")
                                        # delete original file
                                        os.remove(file_path)
                                        logger.info(f"Deleted {file_name}")
                                    except Exception as e:
                                        logger.error(f"Error copying {file_name} to {new_file_path}: {e}")
                        else:
                            if dry_run:
                                logger.info(f"[DRY RUN] Would delete {file_name} (unsupported format)")
                            else:
                                os.remove(file_path)
                                logger.info(f"Deleted {file_name} (unsupported format)")

                if dry_run:
                    logger.warning(f"[DRY RUN] Would remove empty folder: {folder_path}")
                else:
                    try:
                        if not os.listdir(folder_path):
                            shutil.rmtree(folder_path)
                            logger.info(f"Removed empty folder: {folder_path}")
                    except Exception as e:
                        logger.error(f"Error removing empty folder: {folder_path}: {e}")
            else:
                logger.info(f"No match for: {folder_name}")

                if dry_run:
                    logger.warning(f"[DRY RUN] Would leave unmatched folder: {folder_path}")
                else:
                    if not os.listdir(folder_path):
                        shutil.rmtree(folder_path)
                        logger.info(f"Removed empty folder: {folder_path}")


if __name__ == "__main__":
    # Usage example
    root_folder = r"\\192.168.0.101\download\downloads\Movies"
    destination_root = r"\\192.168.0.101\download\downloads\ORG_Movies"

    dry_run = False  # Set False to perform actual file operations

    print("Moving unorganized movies to organized folder")
    organize_movies(root_folder, destination_root, dry_run)
