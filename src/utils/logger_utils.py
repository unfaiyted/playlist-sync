import os

from src.config import Config
from src.utils.logger import setup_logger


def get_action_logger(action_name):
    log_dir = os.path.join(Config.CONFIG_DIR, 'logs')
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"{action_name}.log")
    return setup_logger(name=action_name, log_file=log_file)


__all__ = ['get_action_logger']