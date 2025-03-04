# codebase/emby-scripts/src/utils/logger.py
import codecs
import logging
import os
import sys

from src.config import Config
from logging.handlers import RotatingFileHandler
from colorama import Fore, Style, init

init(autoreset=True)


class ColoredFormatter(logging.Formatter):
    COLORS = {
        'DEBUG': Fore.BLUE,
        'WARNING': Fore.YELLOW,
        'INFO': Fore.WHITE,
        'ERROR': Fore.RED,
        'CRITICAL': Fore.RED + Style.BRIGHT
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, Fore.WHITE)
        log_message = super().format(record)
        log_message = log_message.encode('ascii', 'replace').decode('ascii')
        return f"{log_color}{log_message}{Style.RESET_ALL}"


class SafeRotatingFileHandler(RotatingFileHandler):
    def emit(self, record):
        try:
            msg = self.format(record)
            # Ensure the message is a string and handle encoding
            if not isinstance(msg, str):
                msg = str(msg)
            msg = msg.encode('utf-8', 'replace').decode('utf-8')
            self.stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


def setup_logger(name='root', level=logging.DEBUG, log_file=None):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove all handlers associated with the logger object
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler and set formatter
    ch = logging.StreamHandler()
    formatter = ColoredFormatter("%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] -  %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    if log_file:
        file_formatter = logging.Formatter("%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] -  %(message)s")
        file_handler = SafeRotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def get_action_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    # Create console handler with UTF-8 encoding
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - [%(funcName)s:%(lineno)d] - %(message)s')
    ch.setFormatter(formatter)

    # Ensure the logger can handle Unicode
    ch.stream.reconfigure(encoding='utf-8')

    logger.addHandler(ch)
    return logger


# Create a default logger instance
# logger = setup_logger()

# debug = logger.debug
# info = logger.info
# warning = logger.warning
# error = logger.error
# critical = logger.critical
