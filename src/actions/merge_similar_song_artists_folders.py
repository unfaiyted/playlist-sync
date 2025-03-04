import os
import musicbrainzngs

from src.clients.lidarr_client import LidarrClient
from src.utils.file_utils import FileUtils
from src.utils.logger import get_action_logger
from rapidfuzz import fuzz, process

logger = get_action_logger("merge_similar_artist_folders")

FUZZY_MATCH_THRESHOLD = 91  # 91% similarity threshold for merging

# Set up MusicBrainz API
musicbrainzngs.set_useragent("YourAppName", "0.1", "your@email.com")


def get_primary_artist(folder_name, music_dir, known_artists):
    """
    Determine the primary artist for a given folder name.
    """
    # First, check if the folder name exactly matches a known artist
    if folder_name in known_artists:
        return folder_name

    for artist in music_dir:
        if artist.lower() == folder_name.lower():
            return artist

    # If not, try to find a close match
    matches = process.extract(folder_name, known_artists, scorer=fuzz.ratio, limit=1)
    if matches and matches[0][1] >= 95:  # Only suggest a rename if the match is very close
        return matches[0][0]

    # If no close match is found, return the original folder name
    return folder_name


def rename_artist_folders(lidarr, music_dir, dry_run=False):
    known_artists = lidarr.get_artists()
    logger.info(f"Fetched {len(known_artists)} known artists from Lidarr")

    for folder in os.listdir(music_dir):
        if os.path.isdir(os.path.join(music_dir, folder)):
            primary_artist = get_primary_artist(folder, music_dir, known_artists)
            if primary_artist.lower() != folder.lower():
                old_path = os.path.join(music_dir, folder)
                new_path = os.path.join(music_dir, primary_artist)

                # Additional check to prevent renaming to an existing folder
                if os.path.exists(new_path):
                    logger.warning(f"Cannot rename {old_path} to {new_path} as destination already exists")
                    continue

                if dry_run:
                    logger.info(f"[DRY RUN] Would rename {old_path} to {new_path}")
                else:
                    try:
                        os.rename(old_path, new_path)
                        logger.info(f"Renamed {old_path} to {new_path}")
                    except Exception as e:
                        logger.error(f"Error renaming {old_path} to {new_path}: {str(e)}")


# def get_primary_artist(folder_name, music_dir):
#     words = folder_name.split()
#     potential_artists = []
#
#     # Sliding window approach
#     for window_size in range(1, len(words) + 1):
#         for i in range(len(words) - window_size + 1):
#             potential_artist = " ".join(words[i:i+window_size])
#             potential_artists.append(potential_artist)
#
#     # Check against MusicBrainz API
#     for artist in potential_artists:
#         try:
#             result = musicbrainzngs.search_artists(artist=artist, limit=1)
#             if result['artist-list']:
#                 return result['artist-list'][0]['name']
#         except musicbrainzngs.WebServiceError:
#             pass  # Continue if API call fails
#
#     # Frequency analysis of file contents
#     artist_counter = Counter()
#     folder_path = os.path.join(music_dir, folder_name)
#     for file in os.listdir(folder_path):
#         if file.endswith('.mp3'):  # Adjust for other music file types
#             file_words = file.split(' - ')[0].split()  # Assuming "Artist - Title" format
#             artist_counter.update([" ".join(file_words[:i]) for i in range(1, len(file_words) + 1)])
#
#     if artist_counter:
#         return artist_counter.most_common(1)[0][0]
#
#     # Fallback: Return the first word(s) that match any known artist
#     known_artists = get_known_artists()  # Implement this function to get a list of known artists
#     for i in range(len(words), 0, -1):
#         potential_artist = " ".join(words[:i])
#         matches = process.extract(potential_artist, known_artists, scorer=fuzz.ratio, limit=1)
#         if matches and matches[0][1] > 90:  # 90% similarity threshold
#             return matches[0][0]
#
#     # If all else fails, return the first word
#     return words[0]

# def merge_folders(src, dst, dry_run=False):
#     """Merge source folder into destination folder."""
#     logger.info(f"Merging {src} into {dst}")
#
#     # IF source and destination are the same, skip
#     if src == dst:
#         logger.warning(f"Source and destination are the same, skipping {src}")
#         return
#
#     for item in os.listdir(src):
#         s = os.path.join(src, item)
#         d = os.path.join(dst, item)
#         if os.path.isdir(s):
#             if not os.path.exists(d):
#                 FileUtils.safe_move(logger, s, d, dry_run)
#             else:
#                 merge_folders(s, d, dry_run)
#         else:
#             if not os.path.exists(d):
#                 FileUtils.safe_move(logger, s, d, dry_run)
#             else:
#                 logger.warning(f"File {s} already exists, deleting if different src/dest...")
#                 if os.path.exists(d):
#                     if s == d:
#                         logger.warning(f"Source and destination are the same, skipping {s}")
#                     elif os.path.getsize(s) == os.path.getsize(d):
#                         logger.warning(f"File sizes same, deleting {s}")
#                         if not dry_run:
#                             os.remove(s)
#                         else:
#                             logger.info(f"[DRY RUN] Would delete {s}")
#                     else:
#                         logger.warning(f"File sizes do not match,  skipping... {s}")
#
#     try:
#         os.rmdir(src)
#         logger.info(f"Removed empty directory: {src}")
#     except OSError:
#         logger.warning(f"Could not remove directory: {src}")


def merge_similar_artist_folders(lidarr, music_dir, dry_run=False):
    logger.info(f"Starting to merge similar artist folders in {music_dir}")
    artist_folders = FileUtils.get_directories(music_dir)
    logger.info(f"Found {len(artist_folders)} artist folders")
    known_artists = lidarr.get_artists()
    merged_folders = set()

    for i, folder in enumerate(artist_folders):
        if folder in merged_folders:
            continue

        primary_artist = get_primary_artist(folder, music_dir, known_artists)
        if primary_artist != folder:
            src = os.path.join(music_dir, folder)
            dst = os.path.join(music_dir, primary_artist)

            if dry_run:
                logger.info(f"[DRY RUN] Would merge {src} into {dst}")
            else:
                logger.info(f"Merging {src} into {dst}")
                FileUtils.merge_folders(src, dst, dry_run)

            merged_folders.add(folder)
            merged_folders.add(primary_artist)
        else:
            # Only look for similar folders if we didn't find a primary artist match
            matches = process.extract(
                folder,
                artist_folders[i + 1:],
                scorer=fuzz.ratio,
                limit=None,
                score_cutoff=FUZZY_MATCH_THRESHOLD
            )

            for match_info in matches:
                if len(match_info) == 2:
                    match, score = match_info
                elif len(match_info) == 3:
                    match, score, _ = match_info
                else:
                    logger.warning(f"Unexpected match_info: {match_info}")
                    continue

                logger.info(f"Found match: {match} (similarity: {score}%)")
                if match not in merged_folders:
                    src = os.path.join(music_dir, match)
                    dst = os.path.join(music_dir, folder)

                    if dry_run:
                        logger.info(f"[DRY RUN] Would merge {src} into {dst} (similarity: {score}%)")
                    else:
                        logger.info(f"Merging {src} into {dst} (similarity: {score}%)")
                        FileUtils.merge_folders(src, dst, dry_run)

                    merged_folders.add(match)

        merged_folders.add(folder)

    logger.info(f"Merged {len(merged_folders)} folders")


if __name__ == "__main__":
    # music_dir = Config.MUSIC_STORAGE_DIR  # Assuming you have this in your Config
    music_dir = r"X:\music"
    dry_run = True  # Set to True for a dry run

    logger.info(f"Starting to merge similar artist folders in {music_dir}")
    lidarr = LidarrClient()
    merge_similar_artist_folders(lidarr, music_dir, dry_run)
    rename_artist_folders(lidarr, music_dir, dry_run)
    logger.info("Finished merging similar artist folders")
