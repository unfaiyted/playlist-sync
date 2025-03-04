import os
import shutil
import argparse
import re
from mutagen import File
from mutagen.easyid3 import EasyID3
from src.utils.logger import get_action_logger
logger = get_action_logger("sort_downloaded_albums")

AUDIO_EXTENSIONS = ('.flac', '.mp3', '.m4a', '.wav', '.ogg', '.aac')

def clean_artist_name(artist):
    # Remove 'ft', 'feat', 'feature' and anything following
    cleaned = re.split(r'\s+(?:ft\.?|feat\.?|feature)', artist, flags=re.IGNORECASE)[0]
    # Remove special characters except spaces, hyphens, and underscores
    cleaned = ''.join(c for c in cleaned if c.isalnum() or c in ' -_')
    return cleaned.strip()

def get_metadata(file_path):
    try:
        if file_path.lower().endswith('.mp3'):
            try:
                audio = EasyID3(file_path)
                artist = audio.get('artist', [None])[0]
                album = audio.get('album', [None])[0]
            except Exception as e:
                logger.warning(f"Error reading metadata from {file_path}: {str(e)}. Trying to read ID3 tags from file.")
                audio = File(file_path)
                artist = audio.get('artist', [None])[0] if audio else None
                album = audio.get('album', [None])[0] if audio else None

        else:
            audio = File(file_path)
            artist = audio.get('artist', [None])[0]
            album = audio.get('album', [None])[0]

        if artist:
            artist = clean_artist_name(artist)

        if artist and album:
            return artist, album
        else:
            logger.warning(f"Incomplete metadata for {file_path}. Artist: {artist}, Album: {album}")
            return None, None
    except Exception as e:
        logger.error(f"Error reading metadata from {file_path}: {str(e)}")
        return None, None

def delete_empty_folders(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            try:
                if not os.listdir(dir_path):
                    try:
                        os.rmdir(dir_path)
                        logger.info(f"Deleted empty folder: {dir_path}")
                    except Exception as e:
                        logger.error(f"Error deleting empty folder {dir_path}: {str(e)}")
            except Exception as e:
                logger.error(f"Error listing files in {dir_path}: {str(e)}")

async def organize_music(source_dir, destination_dir, dry_run=True):
    logger.info(f"Organizing music in {source_dir} to {destination_dir}")

    # Count total number of folders
    total_folders = sum([len(dirs) for _, dirs, _ in os.walk(source_dir)])
    processed_folders = 0

    if total_folders == 0:
        logger.warning("No folders found in source directory. Exiting.")
        return

    for root, dirs, files in os.walk(source_dir):
        processed_folders += 1
        progress_percentage = (processed_folders / total_folders) * 100
        logger.info(f"Processing folder {processed_folders}/{total_folders} ({progress_percentage:.2f}%): {root}")

        for file in files:
            logger.debug(f"Checking {file}")
            file_path = os.path.join(root, file)

            if file.lower().endswith(AUDIO_EXTENSIONS):
                artist, album = get_metadata(file_path)

                if artist is None or album is None:
                    logger.warning(f"Skipping {file_path} due to missing metadata")
                    continue

                # Clean up album name
                album = ''.join(c for c in album if c.isalnum() or c in ' -_')

                new_dir = os.path.join(destination_dir, artist, album)
                new_file_path = os.path.join(new_dir, file)

                if dry_run:
                    logger.info(f"[DRY RUN] Would move {file_path} to {new_file_path}")
                else:
                    try:
                        os.makedirs(new_dir, exist_ok=True)
                        shutil.move(file_path, new_file_path)
                        logger.info(f"Moved {file} to {new_file_path}")
                    except Exception as e:
                        logger.error(f"Error moving {file}: {str(e)}")
            else:
                if dry_run:
                    logger.info(f"[DRY RUN] Would delete non-audio file {file_path}")
                else:
                    try:
                        os.remove(file_path)
                        logger.info(f"Deleted non-audio file {file_path}")
                    except Exception as e:
                        logger.error(f"Error deleting non-audio file {file_path}: {str(e)}")

    if not dry_run:
        delete_empty_folders(source_dir)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Organize music files based on metadata.")
    parser.add_argument("--source", default=r"\\192.168.0.101\download\downloads\music",
                        help="Source directory containing music files")
    parser.add_argument("--destination", default=r"\\192.168.0.101\download\downloads\organized_music",
                        help="Destination directory for organized music")
    parser.add_argument("--dry-run", action="store_true", help="Perform a dry run without moving files")
    args = parser.parse_args()

    logger.info("Starting music organization process...")
    logger.info(f"Source directory: {args.source}")
    logger.info(f"Destination directory: {args.destination}")
    # args.dry_run = True
    logger.info(f"Dry run: {'Yes' if args.dry_run else 'No'}")

    organize_music(args.source, args.destination, args.dry_run)

    if args.dry_run:
        logger.info("Dry run complete. No files were moved.")
    else:
        logger.info("Music organization complete.")