# codebase/emby-scripts/src/actions/find_song_lyrics.py
import multiprocessing
import os
import time
from functools import partial

import lyricsgenius
from spotdl import Spotdl
from mutagen import File
from src.utils.logger import get_action_logger
from src.config import Config
import subprocess
import tempfile
import sqlite3
from datetime import datetime, timedelta

logger = get_action_logger("find_song_lyrics")

INITIAL_BACKOFF = 2  # 2 seconds
MAX_BACKOFF = 7200  # 2 hours
current_backoff = INITIAL_BACKOFF

global_conn = None
db_lock = multiprocessing.Lock()

def get_db_connection(config_root="/app/config/"):
    conn = sqlite3.connect(config_root + Config.DATABASE_FILE_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def create_table(config_root="/app/config/"):
    conn = get_db_connection(config_root)
    cursor = conn.cursor()
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS lyrics_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        artist TEXT,
        album TEXT,
        filename TEXT,
        lyrics_found BOOLEAN,
        last_check_date DATE,
        UNIQUE(artist, album, filename)
    )
    ''')

    cursor.execute('CREATE INDEX IF NOT EXISTS idx_artist_album_filename ON lyrics_tracking(artist, album, filename)')
    conn.commit()

def get_metadata(file_path):
    try:
        audio = File(file_path, easy=True)
        if audio is not None:
            title = audio.get('title', [''])[0]
            artist = audio.get('artist', [''])[0]
            album = audio.get('album', [''])[0]
            return title, artist, album
    except Exception as e:
        logger.error(f"Error reading metadata for {file_path}: {str(e)}")
    return None, None, None


def save_lyrics(lyrics, file_path):
    lyrics_file = os.path.splitext(file_path)[0] + '.lrc'
    try:
        with open(lyrics_file, 'w', encoding='utf-8') as f:
            f.write(lyrics)
        logger.info(f"Lyrics saved to {lyrics_file}")
    except Exception as e:
        logger.error(f"Error saving lyrics for {file_path}: {str(e)}")


def get_lyrics_from_genius(title, artist):
    global last_genius_request_time, current_backoff

    current_time = time.time()
    time_since_last_request = current_time - last_genius_request_time

    if time_since_last_request < current_backoff:
        logger.info(f"Genius API rate limit reached. Backing off for {current_backoff} seconds.")
        time.sleep(current_backoff - time_since_last_request)

    try:
        song = genius.search_song(title, artist)
        if song:
            return song.lyrics
    except Exception as e:
        if "429" in str(e):
            logger.warning("Genius API rate limit reached. Switching to PyLyrics.")

            # increase the backoff time each time we hit the rate limit
            current_backoff = min(current_backoff * 2, MAX_BACKOFF)

            return None
        logger.error(f"Error finding lyrics on Genius for {title} by {artist}: {str(e)}")
    return None


def get_lyrics_from_spotdl(title, artist):
    try:
        search_query = f"{title} - {artist}"
        with tempfile.TemporaryDirectory() as temp_dir:
            command = [
                "python -m spotdl",
                "download",
                '"' + search_query + '"',
                "--lyrics", "genius,musixmatch,azlyrics,synced",
                "--output", '"' + temp_dir + '"',
                "--generate-lrc",
                "--print-errors",
                "--log-level", "ERROR",
            ]
            logger.info(f"Running spotdl command: {' '.join(command)}")

            result = subprocess.run(command, capture_output=True, text=True)

            if result.returncode != 0:
                logger.error(f"spotdl command failed: {result.stderr}")
                return None

            # Find the .lrc file in the temporary directory
            lrc_files = [f for f in os.listdir(temp_dir) if f.endswith('.lrc')]

            if not lrc_files:
                logger.warning(f"No lyrics file found for {title} by {artist}")
                return None

            # Read the contents of the first .lrc file
            with open(os.path.join(temp_dir, lrc_files[0]), 'r', encoding='utf-8') as f:
                lyrics = f.read()

            logger.info(f"Found lyrics with spotdl for {title} by {artist}")
            return lyrics
    except Exception as e:
        logger.error(f"Error finding lyrics with spotdl for {title} by {artist}: {str(e)}")
        return None



def find_and_save_lyrics(file_path, config_root):
    conn = get_db_connection(config_root)
    try:
        cursor = conn.cursor()

        title, artist, album = get_metadata(file_path)

        filename = os.path.basename(file_path)

        # Check if we've searched for this song recently
        cursor.execute('''
        SELECT * FROM lyrics_tracking 
        WHERE artist = ? AND album = ? AND filename = ?
        ''', (artist, album, filename))

        record = cursor.fetchone()

        current_date = datetime.now().date()

        if record:
            if record['lyrics_found']:
                logger.info(f"Lyrics already found for {filename}. Skipping.")
                # conn.close()
                return
            elif record['last_check_date']:
                last_check_date = datetime.strptime(record['last_check_date'], '%Y-%m-%d').date()
                if (current_date - last_check_date).days < 7:
                    logger.info(f"Lyrics check for {filename} was performed recently. Skipping.")
                    return

        lrc_file = os.path.splitext(file_path)[0] + '.lrc'
        lyrics_found = False

        if os.path.exists(lrc_file):
            logger.debug(f"Lyrics file already exists for {filename}. Skipping.")
            lyrics_found = True
        else:
            if title and artist:
                logger.info(f"Searching for lyrics on Genius for {title} by {artist}")
                lyrics = get_lyrics_from_genius(title, artist)
                if not lyrics:
                    logger.info(f"Searching for lyrics on Spotdl for {title} by {artist}")
                    lyrics = get_lyrics_from_spotdl(title, artist)

                if lyrics:
                    logger.info(f"Found lyrics for {title} by {artist}")
                    save_lyrics(lyrics, file_path)
                    lyrics_found = True
                else:
                    logger.warning(f"No lyrics found for {title} by {artist}")
            else:
                logger.warning(f"Couldn't extract metadata from {file_path}")

        # Update or insert record in database
        cursor.execute('''
        INSERT OR REPLACE INTO lyrics_tracking 
        (artist, album, filename, lyrics_found, last_check_date)
        VALUES (?, ?, ?, ?, ?)
        ''', (artist, album, filename, lyrics_found, current_date))
        conn.commit()
    finally:
        conn.close()
#
# def process_music_folder(folder_path):
#     logger.info(f"Processing music folder: {folder_path}")
#     for root, _, files in os.walk(folder_path):
#         for file in files:
#             if file.lower().endswith(('.mp3', '.flac', '.m4a', '.wav')):
#                 file_path = os.path.join(root, file)
#                 logger.info(f"Processing {file_path}")
#                 find_and_save_lyrics(file_path)
#                 time.sleep(2)  # Increased delay to be more respectful to the services
#
#
# def process_music_folder(folder_path):
#     logger.info(f"Processing music folder: {folder_path}")
#     for root, _, files in os.walk(folder_path):
#         for file in files:
#             if file.lower().endswith(('.mp3', '.flac', '.m4a', '.wav')):
#                 file_path = os.path.join(root, file)
#                 logger.info(f"Processing {file_path}")
#
#                 lrc_file = os.path.splitext(file_path)[0] + '.lrc'
#                 if os.path.exists(lrc_file):
#                     logger.info(f"Lyrics file already exists for {file_path}. Skipping.")
#                     continue
#
#                 find_and_save_lyrics(file_path)
#                 time.sleep(1)  # Add a small delay to avoid hitting rate limits too quickly


def process_file(file_path, config_root):
    try:
        find_and_save_lyrics(file_path, config_root)
    except Exception as e:
        logger.error(f"Error processing file: {file_path}")
        logger.error(f"Error message: {str(e)}")


def process_music_folder(folder_path, config_root="/app/config/"):
    create_table(config_root)

    file_paths = []
    for entry in os.scandir(folder_path):
        if entry.is_file() and entry.name.lower().endswith(('.mp3', '.flac', '.m4a', '.wav')):
            file_paths.append(entry.path)
        elif entry.is_dir():
            file_paths.extend(process_music_folder(entry.path, config_root))

    # Use multiprocessing to process files in parallel
    with multiprocessing.Pool() as pool:
        pool.map(partial(process_file, config_root=config_root), file_paths)

    logger.info(f"Finished processing {len(file_paths)} files in {folder_path}")

    return file_paths


if __name__ == "__main__":
    # Initialize Genius API client
    genius = lyricsgenius.Genius(Config.GENIUS_ACCESS_TOKEN)

    # Initialize Spotdl client
    spotdl = Spotdl(client_id=Config.SPOTIFY_CLIENT_ID, client_secret=Config.SPOTIFY_CLIENT_SECRET)


    last_genius_request_time = 0

    organized_music_folder = r"\\192.168.0.101\download\music"  # Replace with your organized music folder path
    all_processed_files = process_music_folder(organized_music_folder, config_root="../../config/")
    logger.info(f"Total processed files: {len(all_processed_files)}")
