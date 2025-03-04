import os
import shutil
import mutagen
import requests
from mutagen import File
from mutagen.flac import FLAC
from mutagen.easyid3 import EasyID3
from fuzzywuzzy import fuzz
from src.config import Config
from src.utils.logger import get_action_logger
logger = get_action_logger("move_organized_music")

def clean_name(name):
    return name.strip()


def get_existing_artists(destination_folder):
    existing_artists = {}
    for artist in os.listdir(destination_folder):
        if os.path.isdir(os.path.join(destination_folder, artist)):
            existing_artists[artist] = clean_name(artist)
    return existing_artists


def is_similar_artist(new_artist, existing_artist, threshold=90):

    # remove 'the' from the beginning of the artist name
    new_artist = new_artist.replace('the ', '', 1)
    existing_artist = existing_artist.replace('the ', '', 1)

    return fuzz.ratio(new_artist.lower(), existing_artist.lower()) >= threshold


def get_artist_from_lidarr(artist_name):
    lidarr_url = Config.LIDARR_URL
    lidarr_api_key = Config.LIDARR_API_KEY

    search_url = f"{lidarr_url}/api/v1/artist/lookup"
    params = {"term": artist_name}
    headers = {"X-Api-Key": lidarr_api_key}

    try:
        response = requests.get(search_url, params=params, headers=headers)
        response.raise_for_status()
        search_results = response.json()

        if search_results:
            matched_artist = next(
                (artist for artist in search_results if is_similar_artist(artist_name, artist['artistName'])),
                None
            )
            if matched_artist:
                # Check if the artist is already monitored in Lidarr
                get_artist_url = f"{lidarr_url}/api/v1/artist"
                get_artist_response = requests.get(get_artist_url, headers=headers)
                get_artist_response.raise_for_status()
                existing_artists = get_artist_response.json()

                existing_artist = next((artist for artist in existing_artists if
                                        artist['foreignArtistId'] == matched_artist['foreignArtistId']), None)

                if existing_artist:
                    return existing_artist
                else:
                    # Add the artist to Lidarr
                    add_url = f"{lidarr_url}/api/v1/artist"
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
                    add_response = requests.post(add_url, json=add_data, headers=headers)
                    add_response.raise_for_status()
                    return add_response.json()

    except requests.RequestException as e:
        logger.error(f"Error communicating with Lidarr API: {str(e)}")

    return None


def refresh_artist_in_lidarr(artist_name):
    lidarr_url = Config.LIDARR_URL
    lidarr_api_key = Config.LIDARR_API_KEY

    # Search for the artist in Lidarr
    search_url = f"{lidarr_url}/api/v1/artist/lookup"
    params = {"term": artist_name}
    headers = {"X-Api-Key": lidarr_api_key}

    try:
        response = requests.get(search_url, params=params, headers=headers)
        response.raise_for_status()
        search_results = response.json()

        logger.debug(f"Search results: {search_results}")

        if search_results:
            # Find the exact match or the closest match
            matched_artist = next(
                (artist for artist in search_results if artist['artistName'].lower() == artist_name.lower()), None)

            if matched_artist is None:
                logger.warning(f"No exact match found for artist '{artist_name}'. Searching for closest match...")
                matched_artist = next((artist for artist in search_results if is_similar_artist(artist_name.lower(),
                                                                                                artist[
                                                                                                    'artistName'].lower())),
                                      None)

                if matched_artist is None:
                    logger.warning(f"No closest match found for artist '{artist_name}'. Skipping...")
                    return

            # Check if the artist is already monitored in Lidarr
            get_artist_url = f"{lidarr_url}/api/v1/artist"
            get_artist_response = requests.get(get_artist_url, headers=headers)
            get_artist_response.raise_for_status()
            existing_artists = get_artist_response.json()

            existing_artist = next((artist for artist in existing_artists if
                                    artist['foreignArtistId'] == matched_artist['foreignArtistId']), None)

            if existing_artist:
                artist_id = existing_artist['id']
                logger.info(f"Artist '{artist_name}' found in Lidarr with ID: {artist_id}")
            else:
                # If the artist is not in Lidarr yet, add them
                logger.info(f"Artist '{artist_name}' not found in Lidarr. Adding artist...")
                add_url = f"{lidarr_url}/api/v1/artist"
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
                    "path": os.path.join(Config.MUSIC_STORAGE_DIR, artist_name),
                    "mbId": matched_artist.get('mbId'),
                    "tags": [],
                    "genres": matched_artist.get('genres', []),
                    "status": matched_artist.get('status', 'continuing')
                }
                add_response = requests.post(add_url, json=add_data, headers=headers)
                add_response.raise_for_status()
                artist_id = add_response.json()['id']
                logger.info(f"Artist '{artist_name}' added to Lidarr with ID: {artist_id}")

            # Trigger a refresh for the artist
            refresh_url = f"{lidarr_url}/api/v1/command"
            data = {
                "name": "RefreshArtist",
                "artistId": artist_id
            }

            refresh_response = requests.post(refresh_url, json=data, headers=headers)
            refresh_response.raise_for_status()

            logger.info(f"Triggered refresh for artist '{artist_name}' in Lidarr")
        else:
            logger.warning(f"Artist '{artist_name}' not found in Lidarr search results")

    except requests.RequestException as e:
        logger.error(f"Error communicating with Lidarr API: {str(e)}")


def get_file_metadata(file_path):
    try:
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.mp3':
            try:
                audio = EasyID3(file_path)
            except mutagen.id3.ID3NoHeaderError:
                audio = File(file_path, easy=True)
                if audio is None:
                    return None, None
        elif file_extension == '.flac':
            audio = FLAC(file_path)
        else:
            audio = File(file_path, easy=True)
            if audio is None:
                logger.warning(f"Unsupported file format for {file_path}")
                return None, None

        title = audio.get('title', [''])[0]
        track = audio.get('tracknumber', [''])[0].split('/')[0]  # Get the track number before the total tracks
        return title.lower(), track
    except Exception as e:
        logger.error(f"Error reading metadata for {file_path}: {str(e)}")
    return None, None


def merge_albums(source_album_path, destination_album_path, dry_run=False):
    # Get metadata for all files in the destination album
    dest_files_metadata = {}
    for file in os.listdir(destination_album_path):
        file_path = os.path.join(destination_album_path, file)
        if os.path.isfile(file_path):
            title, track = get_file_metadata(file_path)
            if title and track:
                dest_files_metadata[(title, track)] = file

    for file in os.listdir(source_album_path):
        logger.debug(f"Processing file '{file}'")
        source_file_path = os.path.join(source_album_path, file)
        destination_file_path = os.path.join(destination_album_path, file)

        if os.path.isfile(source_file_path):
            title, track = get_file_metadata(source_file_path)

            if title is None and track is None:
                logger.warning(f"Could not read metadata for '{file}'. Skipping.")
                continue

            if (title, track) in dest_files_metadata:
                existing_file = dest_files_metadata[(title, track)]
                logger.warning(
                    f"File with same metadata (title: '{title}', track: '{track}') already exists as '{existing_file}' in destination. Skipping '{file}'.")
                # delete file since it already exists
                try:
                    os.remove(source_file_path)
                    logger.warning(f"Deleted file '{source_file_path}' since it already exists at destination path '{destination_file_path}'.")
                except OSError:
                    logger.warning(f"Failed to delete file '{source_file_path}'.")
                    continue

            elif not os.path.exists(destination_file_path):
                if dry_run:
                    logger.info(f"[DRY RUN] Would move file '{file}' to '{destination_album_path}'")
                else:
                    shutil.move(source_file_path, destination_file_path)
                    logger.info(f"Moved file '{file}' to '{destination_album_path}'")
            else:
                # File with same name exists, but metadata is different
                logger.warning(f"File '{file}' exists in destination with different metadata. Renaming and moving.")
                base, ext = os.path.splitext(file)
                new_file = f"{base}_new{ext}"
                new_destination_path = os.path.join(destination_album_path, new_file)

                if dry_run:
                    logger.info(f"[DRY RUN] Would move file '{file}' to '{new_destination_path}'")
                else:
                    shutil.move(source_file_path, new_destination_path)
                    logger.info(f"Moved file '{file}' to '{new_destination_path}'")

    # Check for and remove empty subdirectories in the source album
    for root, dirs, files in os.walk(source_album_path, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):
                if dry_run:
                    logger.info(f"[DRY RUN] Would remove empty directory: '{dir_path}'")
                else:
                    os.rmdir(dir_path)
                    logger.info(f"Removed empty directory: '{dir_path}'")


def remove_empty_folders(path, dry_run=False):
    for root, dirs, files in os.walk(path, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if not os.listdir(dir_path):  # Check if the directory is empty
                if dry_run:
                    logger.info(f"[DRY RUN] Would remove empty directory: '{dir_path}'")
                else:
                    try:
                        os.rmdir(dir_path)
                        logger.info(f"Removed empty directory: '{dir_path}'")
                    except OSError as e:
                        logger.error(f"Error removing directory '{dir_path}': {e}")

    # Check if the root folder is empty and remove it if so
    if not os.listdir(path):
        if dry_run:
            logger.info(f"[DRY RUN] Would remove empty root directory: '{path}'")
        else:
            try:
                os.rmdir(path)
                logger.info(f"Removed empty root directory: '{path}'")
            except OSError as e:
                logger.error(f"Error removing root directory '{path}': {e}")


# async def move_organized_music(source_folder, destination_folder, dry_run=False):
#     existing_artists = get_existing_artists(destination_folder)
#
#     for artist_folder in os.listdir(source_folder):
#         source_artist_path = os.path.join(source_folder, artist_folder)
#         if os.path.isdir(source_artist_path):
#             clean_artist_name = clean_name(artist_folder)
#             destination_artist_path = os.path.join(destination_folder, clean_artist_name)
#
#             similar_artist = None
#             for existing_artist, clean_existing_artist in existing_artists.items():
#                 if is_similar_artist(clean_artist_name, clean_existing_artist):
#                     similar_artist = existing_artist
#                     break
#
#             if similar_artist:
#                 logger.warning(
#                     f"Similar artist already exists: '{similar_artist}'. Merging albums for '{clean_artist_name}'.")
#                 destination_artist_path = os.path.join(destination_folder, similar_artist)
#
#             if not os.path.exists(destination_artist_path):
#                 if dry_run:
#                     logger.info(f"[DRY RUN] Would create artist folder: '{clean_artist_name}'")
#                 else:
#                     os.makedirs(destination_artist_path)
#                     logger.info(f"Created artist folder: '{clean_artist_name}'")
#
#             for album_folder in os.listdir(source_artist_path):
#                 source_album_path = os.path.join(source_artist_path, album_folder)
#                 if os.path.isdir(source_album_path):
#                     clean_album_name = clean_name(album_folder)
#                     destination_album_path = os.path.join(destination_artist_path, clean_album_name)
#
#                     if os.path.exists(destination_album_path):
#                         logger.info(
#                             f"Album '{clean_album_name}' already exists for artist '{clean_artist_name}'. Merging...")
#                         merge_albums(source_album_path, destination_album_path, dry_run)
#                     else:
#                         if dry_run:
#                             logger.info(f"[DRY RUN] Would move album '{clean_album_name}' to '{clean_artist_name}'")
#                         else:
#                             try:
#                                 shutil.move(source_album_path, destination_album_path)
#                                 logger.info(f"Moved album '{clean_album_name}' to '{clean_artist_name}'")
#                             except Exception as e:
#                                 logger.error(f"Error moving album '{clean_album_name}' to '{clean_artist_name}': {e}")
#             if not dry_run:
#                 refresh_artist_in_lidarr(clean_artist_name)
#
#             # Remove empty artist folder from source if all albums were moved
#     remove_empty_folders(source_folder, dry_run)
#     # if not os.listdir(source_artist_path):
#     #     if dry_run:
#     #         logger.info(f"[DRY RUN] Would remove empty artist folder: '{artist_folder}'")
#     #     else:
#     #         os.rmdir(source_artist_path)
#     #         logger.info(f"Removed empty artist folder: '{artist_folder}'")
async def move_organized_music(source_folder, destination_folder, dry_run=False):
    for artist_folder in os.listdir(source_folder):
        source_artist_path = os.path.join(source_folder, artist_folder)
        if os.path.isdir(source_artist_path):
            clean_artist_name = clean_name(artist_folder)

            # Check if the artist exists in Lidarr
            lidarr_artist = get_artist_from_lidarr(clean_artist_name)

            if lidarr_artist:
                destination_artist_path = lidarr_artist['path']
                logger.info(f"Artist '{clean_artist_name}' found in Lidarr. Using path: {destination_artist_path}")
            else:
                logger.warning(f"Artist '{clean_artist_name}' not found in Lidarr and couldn't be added. Skipping...")
                continue

            for album_folder in os.listdir(source_artist_path):
                source_album_path = os.path.join(source_artist_path, album_folder)
                if os.path.isdir(source_album_path):
                    clean_album_name = clean_name(album_folder)
                    destination_album_path = os.path.join(destination_artist_path, clean_album_name)

                    if os.path.exists(destination_album_path):
                        logger.info(
                            f"Album '{clean_album_name}' already exists for artist '{clean_artist_name}'. Merging...")
                        merge_albums(source_album_path, destination_album_path, dry_run)
                    else:
                        if dry_run:
                            logger.info(f"[DRY RUN] Would move album '{clean_album_name}' to '{clean_artist_name}'")
                        else:
                            try:
                                shutil.move(source_album_path, destination_album_path)
                                logger.info(f"Moved album '{clean_album_name}' to '{clean_artist_name}'")
                            except Exception as e:
                                logger.error(f"Error moving album '{clean_album_name}' to '{clean_artist_name}': {e}")

            if not dry_run:
                refresh_artist_in_lidarr(clean_artist_name)

    # Remove empty folders in the source directory
    remove_empty_folders(source_folder, dry_run)

    logger.info("Finished moving organized music and removing empty folders.")
    logger.info("Please manually review any remaining files in the source folder.")

if __name__ == "__main__":
    source_folder = r"\\192.168.0.101\download\downloads\ORG_Music"
    destination_folder = r"\\192.168.0.101\download\music"
    dry_run = True  # Set to False to perform actual file operations
    print("Moving organized music to final destination")
    move_organized_music(source_folder, destination_folder, dry_run)
