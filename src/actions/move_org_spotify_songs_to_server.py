# codebase/emby-scripts/src/actions/move_org_spotify_songs_to_server.py

import os
import re
import shutil
from src.utils.logger import get_action_logger
import sys
import filecmp

from src.utils.string_utils import StringUtils

logger = get_action_logger("move_org_spotify_songs_to_server")


async def move_org_spotify_music_to_server(source, destination, dry_run=False):
    for root, dirs, files in os.walk(source):
        logger.info(f"Processing directory: {root}")
        # Create relative path
        rel_path = os.path.relpath(root, source)
        dest_path = os.path.join(destination, rel_path)

        # Create destination directory if it doesn't exist
        if not dry_run:
            os.makedirs(dest_path, exist_ok=True)

        for file in files:
            logger.info(f"Processing file: {file}")
            src_file = os.path.join(root, file)
            dest_file = os.path.join(dest_path, StringUtils.remove_special_characters(file))

            if dry_run:
                logger.info(f"Would copy {src_file} to {dest_file} and then delete {src_file}")
            else:
                try:
                    # Copy the file
                    shutil.copy2(src_file, dest_file)
                    logger.info(f"Copied {src_file} to {dest_file}")

                    # Verify the copy was successful
                    if filecmp.cmp(src_file, dest_file):
                        # Delete the original file
                        os.remove(src_file)
                        logger.info(f"Deleted original file: {src_file}")
                    else:
                        logger.error(f"Copy verification failed for {src_file}. File not deleted.")
                except Exception as e:
                    logger.error(f"Error processing {src_file}: {e}")


if __name__ == "__main__":
    # Set the source and destination directories
    SOURCE_DIR = r"\\192.168.0.101\download\downloads\org_spotdl_downloads"
    DEST_DIR = r"\\192.168.0.101\download\music"
    # Check if --dry-run flag is provided
    # dry_run = "--dry-run" in sys.argv
    dry_run = False

    if dry_run:
        logger.info("Running in dry-run mode. No files will be copied or deleted.")

    # Ensure the destination directory exists
    if not os.path.exists(DEST_DIR):
        logger.error(f"Destination directory does not exist: {DEST_DIR}")
        sys.exit(1)

    logger.info(f"Starting to copy files from {SOURCE_DIR} to {DEST_DIR}")
    move_org_spotify_music_to_server(SOURCE_DIR, DEST_DIR, dry_run)
    logger.info("File copying and deletion process completed.")

    # Clean up empty directories in the source
    if not dry_run:
        for root, dirs, files in os.walk(SOURCE_DIR, topdown=False):
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                if not os.listdir(dir_path):
                    os.rmdir(dir_path)
                    logger.info(f"Removed empty directory: {dir_path}")
    else:
        logger.info("Dry run mode, not removing empty directories.")
