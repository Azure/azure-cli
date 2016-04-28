import os
import logging
from logging.handlers import RotatingFileHandler

CONSOLE_LOG_CONFIGS = [
    # (default)
    {
        'az': logging.WARNING,
        'root': logging.CRITICAL,
    },
    # --verbose
    {
        'az': logging.INFO,
        'root': logging.CRITICAL,
    },
    # --debug
    {
        'az': logging.DEBUG,
        'root': logging.DEBUG,
    }]

AZ_LOGFILE_NAME = 'az.log'
DEFAULT_LOG_DIR = os.path.expanduser(os.path.join('~', '.azure', 'logs'))

DISABLE_LOG_FILE = os.environ.get('AZURE_CLI_DISABLE_LOG_FILE')
LOG_DIR = os.environ.get('AZURE_CLI_LOG_DIR')

def _determine_verbose_level(argv):
    # Get verbose level by reading the arguments.
    # Remove any consumed args.
    verbose_level = 0
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ['--verbose']:
            verbose_level += 1
            argv.pop(i)
        elif arg in ['--debug']:
            verbose_level += 2
            argv.pop(i)
        else:
            i += 1
    # Use max verbose level if too much verbosity specified.
    return verbose_level if verbose_level < len(CONSOLE_LOG_CONFIGS) else len(CONSOLE_LOG_CONFIGS)-1

def _init_console_handlers(root_logger, az_logger, log_level_config):
    console_log_format = logging.Formatter('%(levelname)s: %(message)s')

    root_console_handler = logging.StreamHandler()
    root_console_handler.setFormatter(console_log_format)
    root_console_handler.setLevel(log_level_config['root'])
    root_logger.addHandler(root_console_handler)

    az_console_handler = logging.StreamHandler()
    az_console_handler.setFormatter(console_log_format)
    az_console_handler.setLevel(log_level_config['az'])
    az_logger.addHandler(az_console_handler)

def _get_log_file_path():
    log_dir = LOG_DIR or DEFAULT_LOG_DIR
    if not os.path.isdir(log_dir):
        os.makedirs(log_dir)
    return os.path.join(log_dir, AZ_LOGFILE_NAME)

def _init_logfile_handlers(root_logger, az_logger):
    if DISABLE_LOG_FILE:
        return
    log_file_path = _get_log_file_path()
    logfile_handler = RotatingFileHandler(log_file_path, maxBytes=5*1024*1024, backupCount=5)
    lfmt = logging.Formatter('%(process)d : %(asctime)s : %(name)s :  %(levelname)s : %(message)s')
    logfile_handler.setFormatter(lfmt)
    logfile_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(logfile_handler)
    az_logger.addHandler(logfile_handler)

def configure_logging(argv):
    verbose_level = _determine_verbose_level(argv)
    log_level_config = CONSOLE_LOG_CONFIGS[verbose_level]

    root_logger = logging.getLogger()
    az_logger = logging.getLogger('az')
    # Set the levels of the loggers to lowest level.
    # Handlers can override by choosing a higher level.
    root_logger.setLevel(logging.DEBUG)
    az_logger.setLevel(logging.DEBUG)
    az_logger.propagate = False

    _init_console_handlers(root_logger, az_logger, log_level_config)
    _init_logfile_handlers(root_logger, az_logger)

def get_az_logger(module_name=None):
    return logging.getLogger('az.' + module_name if module_name else 'az')
