import logging

LOG_LEVEL_CONFIGS = [
    # (default)
    {
        'az': logging.WARNING,
        'root': logging.CRITICAL,
    },
    # -v
    {
        'az': logging.INFO,
        'root': logging.CRITICAL,
    },
    # -vv
    {
        'az': logging.DEBUG,
        'root': logging.DEBUG,
    }]

def _determine_verbose_level(argv):
    # Get verbose level by reading the arguments.
    # Remove any consumed args.
    verbose_level = 0
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ['-v', '--verbose']:
            verbose_level += 1
            argv.pop(i)
        elif arg in ['-vv']:
            verbose_level += 2
            argv.pop(i)
        else:
            i += 1
    # Use max verbose level if too much verbosity specified.
    return verbose_level if verbose_level < len(LOG_LEVEL_CONFIGS) else len(LOG_LEVEL_CONFIGS)-1

def _configure_root_logger(log_level_config):
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level_config['root'])

def _configure_az_logger(log_level_config):
    az_logger = logging.getLogger('az')
    az_logger.setLevel(log_level_config['az'])

def _init_console_handler():
    logging.basicConfig(format='%(levelname)s: %(message)s')

def configure_logging(argv):
    verbose_level = _determine_verbose_level(argv)
    log_level_config = LOG_LEVEL_CONFIGS[verbose_level]

    _init_console_handler()
    _configure_root_logger(log_level_config)
    _configure_az_logger(log_level_config)

def get_az_logger(module_name=None):
    return logging.getLogger('az.' + module_name if module_name else 'az')
