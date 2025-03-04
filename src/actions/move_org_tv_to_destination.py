import os
from rapidfuzz import fuzz, process
from src.clients.sonarr_client import SonarrClient
from src.utils.file_utils import FileUtils
from src.utils.logger import get_action_logger
from itertools import product
from src.config import Config
from src.utils.string_utils import StringUtils

logger = get_action_logger("move_org_tv_shows")

def adjust_path_for_network(path):
    """Adjust the Sonarr path to the network path."""
    network_path = path.replace('/raid/tv', Config.TV_STORAGE_DIR)
    return network_path  #.replace('/', '\\')


def move_folders(source, destination, dry_run=False):
    """Move season folders from source to destination, checking for existing episodes."""
    for item in os.listdir(source):
        logger.info(f"Processing {item}")
        s = os.path.join(source, item)
        d = os.path.join(destination, item)

        if os.path.isdir(s):
            if not os.path.exists(d):
                os.makedirs(d)

            for file in os.listdir(s):
                source_file = os.path.join(s, file)
                dest_file = os.path.join(d, file)

                if os.path.isfile(source_file):
                    season, episode = StringUtils.get_episode_info(file)

                    if season and episode:
                        # Check if an episode with the same S**E** exists in the destination
                        existing_files = [f for f in os.listdir(d) if f'S{season}E{episode}' in f.upper()]

                        if existing_files:
                            logger.info(
                                f"Episode S{season}E{episode} already exists in destination. Deleting source file.")
                            if not dry_run:
                                os.remove(source_file)
                        else:
                            logger.info(f"Moving {file} to {dest_file}")
                            if not dry_run:
                                FileUtils.safe_move(logger, source_file, dest_file)
                    else:
                        logger.warning(f"Could not extract episode info from {file}. Moving anyway.")
                        if not dry_run:
                            FileUtils.safe_move(logger, source_file, dest_file)
                elif os.path.isdir(source_file):
                    move_folders(source_file, dest_file)

            # Remove empty source directory
            if not os.listdir(s):
                logger.info(f"Removing empty directory: {s}")
                if not dry_run:
                    os.rmdir(s)
        else:
            logger.warning(f"{s} is not a directory. Skipping.")


def fuzzy_match(show_name, all_titles):
    """
    Find the best fuzzy match for a show name from all possible titles.
    """
    logger.info(f"Attempting to find a fuzzy match for: '{show_name}'")

    original_year = StringUtils.extract_year(show_name)
    name_without_year = ' '.join([word for word in show_name.split() if not word.isdigit() or len(word) != 4])

    variations = [show_name, name_without_year]
    variations.extend(generate_name_variations(show_name))
    variations.extend(generate_name_variations(name_without_year))
    variations = list(set(variations))  # Remove duplicates

    logger.debug(f"Generated {len(variations)} variations of the show name")
    for i, var in enumerate(variations):
        logger.debug(f"Variation {i + 1}: '{var}'")

    best_match = None
    best_score = 0

    for variation in variations:
        logger.debug(f"Checking variation: '{variation}'")

        match = process.extractOne(variation, all_titles.keys(), scorer=fuzz.ratio)

        if match:
            logger.debug(f"Best match for '{variation}': '{match[0]}' with score {match[1]}")

            if match[1] > best_score:
                potential_match = all_titles[match[0]]
                show_year = potential_match.get('year')

                if original_year and show_year:
                    if abs(original_year - show_year) <= 1:
                        best_score = match[1]
                        best_match = potential_match
                        logger.debug(f"New best match: '{best_match['title']}' with score {best_score}")
                    else:
                        logger.debug(f"Year mismatch: folder year {original_year}, show year {show_year}")
                else:
                    best_score = match[1]
                    best_match = potential_match
                    logger.debug(f"New best match: '{best_match['title']}' with score {best_score}")
        else:
            logger.debug(f"No match found for variation: '{variation}'")

    if best_score >= Config.SONARR_MATCH_THRESHOLD:
        logger.info(f"Best match found: '{best_match['title']}' with score {best_score}")
        return best_match
    else:
        logger.info(f"No match found above threshold. Best score was {best_score}")
        return None


def generate_name_variations(show_name):
    words = show_name.lower().split()
    variations = []

    for i, word in enumerate(words):
        if word == 'and':
            variations.append((['and', '&'], i))
        elif word == '&':
            variations.append((['&', 'and'], i))
        else:
            variations.append(([word], i))

    all_combinations = product(*[v[0] for v in variations])
    return [' '.join(combo) for combo in all_combinations]


def move_organized_tv(sonarr, source_folder, dry_run=False):
    all_shows = sonarr.get_all_shows()
    directories = FileUtils.get_directories(source_folder)

    for directory in directories:
        logger.info(f'Processing directory: {directory}')

        best_match = fuzzy_match(directory, all_shows)

        if best_match:
            show = best_match
            if show.get("id"):
                logger.info(f'Found show [{show["title"]}] with id [{show["id"]}]')

                show_path = sonarr.get_show_path(show['id'])
                adjusted_show_path = adjust_path_for_network(show_path)
                source_path = os.path.join(source_folder, directory)

                move_folders(source_path, adjusted_show_path, dry_run)

                if dry_run:
                    logger.info(f'[DRY RUN] Would trigger rescan for series ID: {best_match["id"]}')
                else:
                    rescan_response = sonarr.rescan_series(best_match['id'])
                    logger.info(f'Triggered rescan for series ID: {best_match["id"]} with response: {rescan_response}')
        else:
            logger.warning(f'No matching show found for: {directory}')

        if dry_run:
            logger.info(f'[DRY RUN] Would delete {os.path.join(source_folder, directory)} if empty')
        else:
            directory_path = os.path.join(source_folder, directory)
            if not os.listdir(directory_path):
                try:
                    os.rmdir(directory_path)
                    logger.info(f'Deleted empty directory: {directory_path}')
                except OSError:
                    logger.warning(f'Failed to delete directory: {directory_path}')
            else:
                logger.warning(f'Directory not empty, did not delete: {directory_path}')


if __name__ == "__main__":
    sonarr_client = SonarrClient(logger)
    source_folder = r"\\192.168.0.101\download\downloads\ORG_TV"
    dry_run = False  # Set to True to perform a dry run
    move_organized_tv(sonarr_client, source_folder, dry_run)
