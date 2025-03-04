import os
import shutil
import tinytag
import re
import sys
import filecmp

from src.utils.logger import get_action_logger
logger = get_action_logger('sort_downloaded_spotify_tracks')

# Regex pattern to extract year from date string
year_pattern = r"\d{4}"


def shorten_album_name(album_name, max_length=50):
    # Remove common words and abbreviate
    album_name = re.sub(r'\bOriginal\s+|Television\s+|Soundtrack\s+|\bOST\b', '', album_name, flags=re.IGNORECASE)
    album_name = album_name.replace('Season', 'S').replace('Special', 'Sp')

    # Remove text in square brackets
    album_name = re.sub(r'\[.*?\]', '', album_name).strip()

    # Truncate if still too long
    if len(album_name) > max_length:
        album_name = album_name[:max_length - 3] + '...'

    return album_name.strip()


def sanitize_filename(filename, max_length=100):
    # Replace problematic characters with underscores
    sanitized = re.sub(r'[<>:"/\\|?*]', "_", filename)
    # Remove trailing dots and spaces
    sanitized = sanitized.rstrip('. ')

    # Truncate if too long
    if len(sanitized) > max_length:
        base, ext = os.path.splitext(sanitized)
        sanitized = base[:max_length - len(ext) - 3] + '...' + ext

    return sanitized or "Unknown"


def process_file(file_path, output_file_path, dry_run=False):
    if os.path.exists(output_file_path):
        if filecmp.cmp(file_path, output_file_path):
            logger.info(f"File already exists and is identical: {output_file_path}")
            return True
        else:
            logger.warning(f"File exists but is different: {output_file_path}")
            return False

    if not dry_run:
        try:
            shutil.copy2(file_path, output_file_path)
            logger.info(f"Copied {file_path} to {output_file_path}")
            return True
        except Exception as e:
            logger.error(f"Error copying {file_path} to {output_file_path}: {e}")
            return False
    else:
        logger.info(f"Dry run: Would have copied {file_path} to {output_file_path}")
        return True


async def sort_downloaded_spotify_tracks(input_dir, output_dir, dry_run=False, keep_source=False):
    for root, dirs, files in os.walk(input_dir):
        for file in files:
            if file.endswith(".mp3"):
                file_path = os.path.join(root, file)

                try:
                    tag = tinytag.TinyTag.get(file_path)
                    artists = [artist.strip() for artist in (tag.artist or "Unknown Artist").split("/")]
                    album = tag.album or "Unknown Album"
                    year_str = str(tag.year) if tag.year else ""
                    year = re.search(year_pattern, year_str).group() if year_str else ""
                    track_number = str(tag.track).zfill(2) if tag.track else "00"
                    title = tag.title or os.path.splitext(file)[0]
                except Exception as e:
                    artists = ["Unknown Artist"]
                    album = "Unknown Album"
                    year = ""
                    track_number = "00"
                    title = os.path.splitext(file)[0]
                    logger.warning(f"Error reading metadata from {file_path}: {e}")

                album_name = f"{album} ({year})" if year else album
                album_name = shorten_album_name(album_name)
                album_name = sanitize_filename(album_name)
                output_artist_dir = os.path.join(output_dir, sanitize_filename(artists[0], max_length=30))
                output_album_dir = os.path.join(output_artist_dir, album_name.replace("_", " "))

                if not os.path.exists(output_album_dir) and not dry_run:
                    try:
                        os.makedirs(output_album_dir)
                        logger.info(f"Created directory: {output_album_dir}")
                    except Exception as e:
                        logger.error(f"Error creating directory: {output_album_dir}: {e}")
                        continue

                new_file_name = f"{track_number} - {sanitize_filename(title, max_length=50)}.mp3"
                output_file_path = os.path.join(output_album_dir, new_file_name)

                if process_file(file_path, output_file_path, dry_run):
                    if not keep_source and not dry_run:
                        try:
                            os.remove(file_path)
                            logger.info(f"Deleted source file: {file_path}")
                        except Exception as e:
                            logger.error(f"Error deleting source file {file_path}: {e}")

                # Process lyrics file
                lyrics_file = os.path.splitext(file)[0] + ".lrc"
                lyrics_file_path = os.path.join(root, lyrics_file)
                if os.path.exists(lyrics_file_path):
                    output_lyrics_file_path = os.path.join(output_album_dir,
                                                           os.path.splitext(new_file_name)[0] + ".lrc")
                    if process_file(lyrics_file_path, output_lyrics_file_path):
                        if not keep_source and not dry_run:
                            try:
                                os.remove(lyrics_file_path)
                                logger.info(f"Deleted source lyrics file: {lyrics_file_path}")
                            except Exception as e:
                                logger.error(f"Error deleting source lyrics file {lyrics_file_path}: {e}")

    # Clean up empty directories in the source if deleting source files
    if not keep_source and not dry_run:
        for root, dirs, files in os.walk(input_dir, topdown=False):
            for dir in dirs:
                dir_path = os.path.join(root, dir)
                if not os.listdir(dir_path):
                    try:
                        os.rmdir(dir_path)
                        logger.info(f"Removed empty directory: {dir_path}")
                    except Exception as e:
                        logger.error(f"Error removing empty directory {dir_path}: {e}")


if __name__ == "__main__":
    # Usage example

    # Set the input and output directories
    input_dir = r"C:\Music\spotdl_downloads"
    output_dir = r"C:\Music\org_spotdl_downloads"

    # Set the dry run and delete source options based on command-line arguments
    dry_run = "--dry-run" in sys.argv
    keep_source = "--dont-delete-source" in sys.argv

    dry_run = False  # Set False to perform actual file operations

    print("Moving unorganized music to organized folder")
    sort_downloaded_spotify_tracks(input_dir, output_dir, dry_run)
