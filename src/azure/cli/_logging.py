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
    # TODO: WRITE TESTS FOR THIS
    while i < len(argv):
        arg = argv[i]
        if arg in ['-v', '--verbose']:
            verbose_level += 1
            argv.pop(i)
        elif arg in ['-vv'] and verbose_level == 0:
            verbose_level = 2
            argv.pop(i)
        else:
            i += 1
    return verbose_level

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
    
    try:
        log_level_config = LOG_LEVEL_CONFIGS[verbose_level]
    except IndexError:
        log_level_config = LOG_LEVEL_CONFIGS[0]

    _init_console_handler()
    _configure_root_logger(log_level_config)
    _configure_az_logger(log_level_config)

def getAzLogger(module_name):
    return logging.getLogger('az.'+module_name)
