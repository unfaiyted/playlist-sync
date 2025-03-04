# codebase/emby-scripts/src/actions/identify_music_with_missing_metadata.py

import os
import time
import acoustid
import requests
from requests.exceptions import RequestException, Timeout
import asyncio
import musicbrainzngs
import mutagen
from mutagen import File
from mutagen.easyid3 import EasyID3
from mutagen.id3 import ID3, APIC
from mutagen.flac import Picture
import signal
from functools import wraps

from mutagen.flac import FLAC
from src.utils.logger import get_action_logger
from dotenv import load_dotenv

logger = get_action_logger("identify_music_with_missing_metadata")
# Replace with your AcoustID API key
ACOUSTID_API_KEY = "Mum6GsimNu"

# Set up MusicBrainz
musicbrainzngs.set_useragent("YourAppName", "0.1", "your@email.com")

# Rate limiting variables
RATE_LIMIT = 3  # requests per second
RATE_LIMIT_PERIOD = 1  # second
last_request_time = 0

# check if on windows
if os.name == 'nt':
    # logger.warning("On Windows, this script may not work as expected. Please use a Linux-based system.")
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", "..", ".env"))
    logger.info("Loading environment variables from .env file...")
    logger.info("FPCALC: " + os.getenv("FPCALC"))


def rate_limited_request(func, *args, **kwargs):
    global last_request_time
    current_time = time.time()
    time_since_last_request = current_time - last_request_time
    if time_since_last_request < RATE_LIMIT_PERIOD / RATE_LIMIT:
        sleep_time = (RATE_LIMIT_PERIOD / RATE_LIMIT) - time_since_last_request
        time.sleep(sleep_time)
    last_request_time = time.time()
    return func(*args, **kwargs)


def timeout_handler(signum, frame):
    raise TimeoutError("Function call timed out")



# This will only work on Linux and macOS
def timeout(seconds):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(seconds)
            try:
                result = func(*args, **kwargs)
            finally:
                signal.alarm(0)
            return result

        return wrapper

    return decorator


@timeout(20)  # Set timeout to 20 seconds
def get_image_list_with_timeout(mb_release_id):
    return musicbrainzngs.get_image_list(mb_release_id)


def fetch_album_art(mb_release_id, timeout=20):
    try:
        release = get_image_list_with_timeout(mb_release_id)
        if release.get('images'):
            for image in release['images']:
                if image['front']:
                    try:
                        response = requests.get(image['image'], timeout=timeout)
                        response.raise_for_status()
                        return response.content
                    except Timeout:
                        logger.warning(f"Timeout while fetching album art for release {mb_release_id}")
                    except RequestException as e:
                        logger.warning(f"Error fetching album art for release {mb_release_id}: {str(e)}")
    except Exception as e:
        logger.error(f"Error fetching album art info for release {mb_release_id}: {str(e)}")
    return None


def identify_track(file_path):
    try:
        logger.info(f"Attempting to generate fingerprint for: {file_path}")
        duration, fingerprint = acoustid.fingerprint_file(file_path)
        logger.info(f"Fingerprint generated successfully for: {file_path}")

        logger.info(f"Looking up fingerprint for: {file_path}")
        lookup_results = rate_limited_request(acoustid.lookup, ACOUSTID_API_KEY, fingerprint, duration)
        logger.info(f"Lookup completed for: {file_path}")

        logger.debug(f"Raw lookup results: {lookup_results}")

        if lookup_results.get('status') != 'ok':
            logger.warning(f"AcoustID lookup failed for: {file_path}")
            return None

        results = lookup_results.get('results', [])
        if not results:
            logger.warning(f"No results found for: {file_path}")
            return None

        for result in results:
            if 'recordings' in result and result['recordings']:
                musicbrainz_id = result['recordings'][0]['id']
                logger.info(f"Fetching MusicBrainz data for: {file_path}")
                mb_result = rate_limited_request(musicbrainzngs.get_recording_by_id, musicbrainz_id,
                                                 includes=['artists', 'releases'])
                logger.info(f"MusicBrainz data fetched for: {file_path}")
                logger.debug(f"MusicBrainz result: {mb_result}")

                if 'recording' in mb_result:
                    # Find the release that matches the recording
                    matching_release = next((release for release in mb_result['recording'].get('release-list', [])
                                             if release['id'] == mb_result['recording']['release-list'][0]['id']), None)

                    # Get the track number if available
                    track_number = None
                    if matching_release:
                        medium_list = matching_release.get('medium-list', [])
                        for medium in medium_list:
                            track_list = medium.get('track-list', [])
                            for track in track_list:
                                if track.get('recording', {}).get('id') == mb_result['recording']['id']:
                                    track_number = track.get('number')
                                    break
                            if track_number:
                                break

                    return {
                        'title': mb_result['recording'].get('title', ''),
                        'artist': mb_result['recording'].get('artist-credit-phrase', ''),
                        'album': mb_result['recording'].get('release-list', [{}])[0].get('title', '') if mb_result[
                            'recording'].get('release-list') else None,
                        'year': mb_result['recording'].get('release-list', [{}])[0].get('date', '')[:4] if mb_result[
                                                                                                               'recording'].get(
                            'release-list') and 'date' in mb_result['recording']['release-list'][0] else None,
                        'release_id': mb_result['recording'].get('release-list', [{}])[0].get('id') if mb_result[
                            'recording'].get('release-list') else None,
                        'track_number': track_number
                    }
                else:
                    logger.warning(f"Unexpected MusicBrainz result structure for: {file_path}")
            else:
                logger.warning(f"No recordings found in result for: {file_path}")

        logger.warning(f"No valid recordings found in any result for: {file_path}")

    except acoustid.FingerprintGenerationError as e:
        logger.error(f"Could not generate fingerprint for file: {file_path}. Error: {str(e)}")
    except acoustid.WebServiceError as exc:
        logger.error(f"Web service error while identifying file: {file_path}. Error: {exc}")
    except musicbrainzngs.ResponseError as exc:
        logger.error(f"Error fetching MusicBrainz data for file: {file_path}. Error: {exc}")
    except Exception as e:
        logger.error(f"Unexpected error processing file: {file_path}. Error: {str(e)}")
        logger.exception("Traceback:")

    return None


def update_metadata(file_path, metadata):
    try:
        file_extension = os.path.splitext(file_path)[1].lower()

        if file_extension == '.mp3':
            try:
                audio = EasyID3(file_path)
            except mutagen.id3.ID3NoHeaderError:
                audio = File(file_path, easy=True)
                audio.add_tags()
        elif file_extension == '.flac':
            audio = FLAC(file_path)
        else:
            logger.warning(f"Unsupported file format for {file_path}")
            return

        if metadata.get('title'):
            audio['title'] = metadata['title']
        if metadata.get('artist'):
            audio['artist'] = metadata['artist']
        if metadata.get('album'):
            audio['album'] = metadata['album']
        if metadata.get('year'):
            if file_extension == '.mp3':
                audio['date'] = metadata['year']
            else:  # FLAC
                audio['year'] = metadata['year']
        if metadata.get('track_number'):
            audio['tracknumber'] = metadata['track_number']

        if metadata.get('release_id'):
            album_art = fetch_album_art(metadata['release_id'])
            if album_art:
                if file_extension == '.mp3':
                    audio = ID3(file_path)
                    audio.add(APIC(encoding=3, mime='image/jpeg', type=3, desc='Cover', data=album_art))
                elif file_extension == '.flac':
                    picture = Picture()
                    picture.type = 3
                    picture.mime = 'image/jpeg'
                    picture.data = album_art
                    audio.add_picture(picture)
            else:
                logger.warning(f"No album art found for release {metadata['release_id']} for file: {file_path}")

        audio.save()
        logger.info(f"Updated metadata for {file_path}")

    except Exception as e:
        logger.error(f"Error updating metadata for {file_path}: {str(e)}")
        logger.exception("Traceback:")


async def match_metadata_unorg_music_folder(downloads_folder):
    for root, _, files in os.walk(downloads_folder):
        for file in files:
            if file.lower().endswith(('.mp3', '.flac', '.m4a', '.wav')):
                file_path = os.path.join(root, file)
                logger.info(f"Processing file: {file_path}")

                try:
                    # Check if the file exists before processing
                    if not os.path.exists(file_path):
                        logger.warning(f"File not found: {file_path}")
                        continue

                    try:
                        if file.lower().endswith('.mp3'):
                            audio = EasyID3(file_path)
                        elif file.lower().endswith('.flac'):
                            audio = FLAC(file_path)
                        else:
                            audio = File(file_path, easy=True)
                    except Exception as e:
                        logger.error(f"Error reading audio file {file_path}: {str(e)}")
                        # delete file
                        # os.remove(file_path)
                        # logger.info(f"Deleted unreadable file: {file_path}")
                        continue

                    if not all(tag in audio for tag in ['title', 'artist', 'album']):
                        logger.info(f"Missing metadata for file: {file_path}")
                        metadata = identify_track(file_path)
                        if metadata:
                            update_metadata(file_path, metadata)
                        else:
                            logger.warning(f"Could not identify metadata for file: {file_path}")
                    else:
                        logger.info(f"Metadata already complete for file: {file_path}")
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {str(e)}")
                    # logger.exception("Traceback:")


if __name__ == "__main__":
    downloads_folder = r"\\192.168.0.101\download\downloads\music"  # Replace with your downloads folder path
    asyncio.run(match_metadata_unorg_music_folder(downloads_folder))
