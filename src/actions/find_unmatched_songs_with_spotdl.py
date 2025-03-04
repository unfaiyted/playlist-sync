# import shlex
import json
import sqlite3
import time
import subprocess
import unicodedata
from src.utils.logger import get_action_logger
from src.config import Config
import re

logger = get_action_logger("find_unmatched_songs_with_spotdl")

def remove_special_characters(string, skip_non_ascii=False):
    if skip_non_ascii and not all(ord(char) < 128 for char in string):
        return None  # Skip strings with non-ASCII characters

    if string is None:
        return ""

    # Normalize Unicode characters
    normalized = unicodedata.normalize('NFKD', string)

    # Remove diacritics (accent marks)
    without_diacritics = ''.join([c for c in normalized if not unicodedata.combining(c)])

    # Replace spaces and other special characters with underscores
    cleaned_string = re.sub(r'[^\w\s-]', '_', without_diacritics)

    # Replace multiple consecutive underscores with a single underscore
    cleaned_string = re.sub(r'_+', '_', cleaned_string)

    # Remove leading and trailing underscores
    cleaned_string = cleaned_string.strip('_')

    # Remove non-ASCII characters
    cleaned_string = cleaned_string.encode('ascii', 'ignore').decode('ascii')

    if cleaned_string == '':
        return None

    return cleaned_string


async def find_unmatched_songs(output_dir, config_root="/app/config/"):
    # Connect to the SQLite database
    conn = sqlite3.connect(config_root + Config.DATABASE_FILE_NAME)
    c = conn.cursor()
    # Create the table to store downloaded songs if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS downloaded_songs
                (track_name TEXT, artist_name TEXT, album_name TEXT)''')

    # Remove duplicates from the unmatched songs table
    c.execute('''DELETE FROM unmatched_songs
                WHERE rowid NOT IN (
                    SELECT MIN(rowid)
                    FROM unmatched_songs
                    GROUP BY track_name, artist_name, album_name
                )''')
    conn.commit()

    # Retrieve the unmatched songs from the database
    c.execute('SELECT DISTINCT track_name, artist_name, album_name FROM unmatched_songs')
    unmatched_songs = c.fetchall()

    # Get the total number of unmatched songs
    total_unmatched_songs = len(unmatched_songs)

    # Process each unmatched song
    for index, song in enumerate(unmatched_songs, start=1):
        track_name, artist_name, album_name = song

        cleaned_track = remove_special_characters(track_name)
        cleaned_artist = remove_special_characters(artist_name)

        # Check if the song has already been downloaded
        c.execute('SELECT COUNT(*) FROM downloaded_songs WHERE track_name = ? AND artist_name = ? AND album_name = ?',
                  (track_name, artist_name, album_name))
        count = c.fetchone()[0]

        if count > 0:
            logger.info(f"Skipping '{track_name}' by {artist_name} - already downloaded")
            continue

        logger.info(f"Processing unmatched song: '{track_name}' by {artist_name}")

        # Use spotdl to find and download the song
        spotdl_path = "python -m spotdl"
        try:
            command = f'{spotdl_path} download "{cleaned_artist} - {cleaned_track}" --output "{output_dir}"'
            logger.info(f"Running command: {command}")


            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)

            logger.info(f"spotdl output: {result}")

            # time.sleep(5)

            if result.returncode == 0:
                logger.info(f"Successfully downloaded '{track_name}' by {artist_name}")

                # Insert the downloaded song into the database
                c.execute('INSERT INTO downloaded_songs VALUES (?, ?, ?)', (track_name, artist_name, album_name))
                conn.commit()
            else:
                logger.error(f"Error downloading '{track_name}' by {artist_name}")
                logger.error(f"Error message: {str(e)}")

            logger.info(f"Successfully downloaded '{track_name}' by {artist_name}")
        except subprocess.CalledProcessError as e:
            logger.error(f"Error downloading '{track_name}' by {artist_name}")
            logger.error(f"Error message: {str(e)}")
        except json.JSONDecodeError:
            logger.error(f"Error parsing spotdl output for '{track_name}' by {artist_name}")
        except Exception as e:
            logger.error(f"Unexpected error downloading '{track_name}' by {artist_name}")
            logger.error(f"Error message: {str(e)}")

        # Calculate the percentage of songs processed
        percentage = (index / total_unmatched_songs) * 100
        logger.info(f"Progress: {index}/{total_unmatched_songs} ({percentage:.2f}%)")

    # Close the database connection
    conn.close()


if __name__ == '__main__':
    # # Set the path to the spotdl.exe file
    # spotdl_path = "C:\\Users\\Dane Miller\\Downloads\\spotdl-4.2.5-win32.exe"

    # # Set the output directory where the songs will be saved
    output_dir = "C:\\Music\\spotdl_downloads"
    find_unmatched_songs(output_dir)
