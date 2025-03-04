import os
import subprocess


class FileUtils:
    @staticmethod
    def safe_move(logger, src, dst, dry_run=False):
        """Safely move a file from src to dst, even across CIFS mounts."""

        if src == dst:
            logger.info(f"Source and destination are the same, skipping move")
            return

        if dry_run:
            logger.info(f'[DRY RUN] Would move {src} to {dst}')
            return

        try:
            # First, try a simple rename (which might work within the same CIFS mount)
            os.rename(src, dst)
            logger.info(f'Moved {src} to {dst}')
        except OSError:
            # If rename fails, use rsync for efficient copy, then remove source
            logger.info(f"Rename failed, using rsync to move {src} to {dst}")
            try:
                # Ensure the destination directory exists
                os.makedirs(os.path.dirname(dst), exist_ok=True)

                # Use rsync to copy
                result = subprocess.run(['rsync', '-av', '--remove-source-files', src, dst],
                                        check=True, capture_output=True, text=True)
                logger.info(f'Moved {src} to {dst} using rsync')
                logger.debug(result.stdout)
            except subprocess.CalledProcessError as e:
                logger.error(f'Error moving {src} to {dst}: {e}')
                logger.error(f'rsync stderr: {e.stderr}')
                # raise
            except Exception as e:
                logger.error(f'Error moving {src} to {dst}: {e}')
                # raise

    @staticmethod
    def merge_folders(logger, src, dst, dry_run=False):
        """Merge source folder into destination folder."""
        logger.info(f"Merging {src} into {dst}")

        if src == dst:
            logger.info(f"Source and destination are the same, skipping merge")
            return

        if dry_run:
            logger.info(f'[DRY RUN] Would merge {src} into {dst}')
            return
        if not os.path.exists(dst):
            logger.info(f"No existing destination folder, moving {src} to {dst}")
            FileUtils.safe_move(logger, src, dst, dry_run=dry_run)
            logger.info(f'Moved {src} to {dst}')
        else:
            logger.info(f"Destination folder exists, merging {src} into {dst}")

            if not os.path.exists(src):
                logger.info(f"No existing source folder, moving {src} to {dst}")
                return

            for item in os.listdir(src):
                s = os.path.join(src, item)
                d = os.path.join(dst, item)
                if os.path.isdir(s):
                    FileUtils.merge_folders(s, d, dry_run)
                else:
                    FileUtils.safe_move(logger, src, dst, dry_run)
                    logger.info(f'Moved {s} to {d}')
            try:
                os.rmdir(src)
                logger.info(f'Removed empty directory: {src}')
            except OSError:
                logger.warning(f'Failed to delete directory: {src}')

    @staticmethod
    def get_directories(path):
        """Get a list of all direct children directories in the given path."""
        return [d for d in os.listdir(path) if os.path.isdir(os.path.join(path, d))]
