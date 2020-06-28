import logging
import sys

from colorama import Fore, Style, init

LEVELS = {
    0: logging.CRITICAL,
    1: logging.ERROR,
    2: logging.WARNING,
    3: logging.INFO,
    4: logging.DEBUG,
    5: logging.NOTSET,
}

MAX_LEVEL = max(LEVELS.keys())
LOGGER = logging.getLogger()


class ToxHandler(logging.StreamHandler):
    def __init__(self, level):
        super().__init__(stream=sys.stdout)
        self.setLevel(level)
        formatter = self._get_formatter(level)
        self.setFormatter(formatter)

    @staticmethod
    def _get_formatter(level):
        msg_format = f"{Style.BRIGHT}{Fore.WHITE}%(name)s: {Fore.CYAN}%(message)s{Style.RESET_ALL}"
        if level <= logging.DEBUG:
            locate = "pathname" if level > logging.DEBUG else "module"
            msg_format += f"{Style.DIM} [%(asctime)s] [%({locate})s:%(lineno)d]{Style.RESET_ALL}"
        formatter = logging.Formatter(msg_format)
        return formatter


def setup_report(verbosity):
    _clean_handlers(LOGGER)
    level = _get_level(verbosity)
    LOGGER.setLevel(level)

    handler = ToxHandler(level)
    LOGGER.addHandler(handler)

    logging.debug("setup logging to %s", logging.getLevelName(level))
    init()


def _get_level(verbosity):
    if verbosity > MAX_LEVEL:
        verbosity = MAX_LEVEL
    level = LEVELS[verbosity]
    return level


def _clean_handlers(log):
    for log_handler in list(log.handlers):  # remove handlers of libraries
        log.removeHandler(log_handler)
