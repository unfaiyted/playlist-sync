import os
import re
import shutil

from src.utils.file_utils import FileUtils
from src.utils.logger import get_action_logger

logger = get_action_logger("move_unorg_tv_to_org")


async def organize_episodes(root_folder, destination_root, dry_run=False):
    # Define known movie file formats
    movie_extensions = [".avi", ".mp4", ".mkv", ".mov", ".wmv"]

    for folder_name in os.listdir(root_folder):
        logger.info('Looking in ' + folder_name)
        folder_path = os.path.join(root_folder, folder_name)
        if os.path.isdir(folder_path):
            match_full = re.match(r"(.+)\.S(\d+)E(\d+)\.(.+)", folder_name, flags=re.IGNORECASE | re.MULTILINE)
            match_season = re.match(r".*(?:S|Season)\s*(\d+).*", folder_name.replace("_", "."), flags=re.IGNORECASE)

            if match_full:
                try:
                    series_name, season_number, episode_number, episode_name = match_full.groups()
                    series_name = series_name.replace(".", " ").strip().title()
                    episode_name = episode_name.replace(".", " ").strip()

                except AttributeError:
                    continue

                season_folder = os.path.join(destination_root, series_name, f"Season {int(season_number):d}")

                logger.info(f"Found full match show:  {series_name} season: {int(season_number):d}")

                if not dry_run:
                    os.makedirs(season_folder, exist_ok=True)

                for file_name in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file_name)
                    if os.path.isfile(file_path):
                        _, extension = os.path.splitext(file_name)
                        if extension.lower() in movie_extensions:
                            new_file_name = f"{series_name} S{season_number.zfill(2)}E{episode_number.zfill(2)} {episode_name.replace('.', ' ')}{extension}"
                            new_file_path = os.path.join(season_folder, new_file_name)

                            if os.path.exists(new_file_path):
                                existing_size = os.path.getsize(new_file_path)
                                new_size = os.path.getsize(file_path)

                                if new_size == existing_size:
                                    logger.info(
                                        f"File {new_file_name} already exists with same size. Deleting unorganized file.")
                                    if not dry_run:
                                        try:
                                            os.remove(file_path)
                                        except OSError:
                                            logger.warning(f"File {file_name} not found. Did not delete.")
                                elif new_size < existing_size:
                                    logger.info(
                                        f"Existing file {new_file_name} is larger. Deleting smaller unorganized file.")
                                    if not dry_run:
                                        os.remove(file_path)
                                else:
                                    logger.info(f"New file {new_file_name} is larger. Replacing existing file.")
                                    if not dry_run:
                                        FileUtils.safe_move(logger, file_path, new_file_path, dry_run=dry_run)
                            else:
                                if dry_run:
                                    logger.info(
                                        f"[DRY RUN] Would move {file_name} to {new_file_path}"
                                    )
                                else:
                                    logger.info(f'Moving {file_name} to {new_file_path}')
                                    FileUtils.safe_move(logger, file_path, new_file_path, dry_run=dry_run)
                        else:
                            if dry_run:
                                logger.info(f"[DRY RUN] Would delete {file_name} (unsupported format)")
                            else:
                                try:
                                    os.remove(file_path)
                                    logger.info(
                                        f"Deleted {file_name} (unsupported format)"
                                    )
                                except FileNotFoundError:
                                    logger.warning(f"File {file_name} not found. Did not delete.")

                if dry_run:
                    logger.warning(f"[DRY RUN] Would remove empty folder: {folder_path}")
                else:
                    try:
                        shutil.rmtree(folder_path)
                        logger.info(f"Removed empty folder: {folder_path}")
                    except FileNotFoundError:
                        logger.warning(f"Folder {folder_path} not found. Did not delete.")
                    except Exception as e:
                        logger.error(f"Error removing empty folder: {folder_path}: {e}")
            elif match_season and not match_full:
                season_number = match_season.groups(1)[0]
                series_name = folder_name.split(f"S{season_number}")[0].replace(".", " ").strip().title()

                logger.info(f"Season {season_number} found match.")

                season_folder = os.path.join(destination_root, series_name, f"Season {season_number}")

                if not dry_run:
                    os.makedirs(season_folder, exist_ok=True)

                for file_name in os.listdir(folder_path):
                    file_path = os.path.join(folder_path, file_name)
                    if os.path.isfile(file_path):
                        _, extension = os.path.splitext(file_name)
                        if extension.lower() in movie_extensions:
                            file_name = file_name.replace("_", ".")
                            # episode_match = re.match(r".*S(\d+)E(\d+)\.(.+)", file_name, flags=re.IGNORECASE)
                            episode_match = re.match(r".*S(\d+)E(\d+).*?([^()]+)(?:\(.*\))?\.(mkv|avi|mp4)$", file_name,
                                                     flags=re.IGNORECASE)

                            if episode_match:
                                logger.info('Found episode match: ' + episode_match.string)
                                season_number, episode_number, episode_name, extra_info = episode_match.groups()
                                episode_name = episode_name.replace(".", " ").replace("_", " ").title()
                                new_file_name = f"{series_name} S{season_number.zfill(2)}E{episode_number.zfill(2)} {episode_name}{extension}"
                                new_file_path = os.path.join(season_folder, new_file_name)

                                if dry_run:
                                    logger.warning(f"[DRY RUN] Would move {file_name} to {new_file_path}")
                                else:
                                    FileUtils.safe_move(logger, file_path, new_file_path, dry_run=dry_run)
                                    logger.info(f"Moved {file_name} to {new_file_path}")
                            else:
                                logger.warning(f"File {file_name} does not match episode pattern and was skipped.")
                        else:
                            if dry_run:
                                logger.warning(f"[DRY RUN] Would delete {file_name} (unsupported format)")
                            else:
                                os.remove(file_path)
                                logger.info(f"Deleted {file_name} (unsupported format)")
            else:
                logger.info("No match")

                if dry_run:
                    logger.warning(f"[DRY RUN] Would remove empty folder: {folder_path}")
                else:
                    if not os.listdir(folder_path):
                        shutil.rmtree(folder_path)
                        logger.info(f"Removed empty folder: {folder_path}")


if __name__ == "__main__":
    # Usage example
    root_folder = r"\\192.168.0.101\download\downloads\TV"
    destination_root = r"\\192.168.0.101\download\downloads\ORG_TV"

    dry_run = False  # Set False to perform actual file operations

    print("Moving unorganized episodes to organized folder")
    organize_episodes(root_folder, destination_root, dry_run)
