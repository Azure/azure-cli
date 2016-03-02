import logging as _logging
import sys

__all__ = ['logger', 'configure_logging']

logger = _logging.Logger('az', _logging.WARNING)

def _arg_name(arg):
    a = arg.lstrip('-/')
    if a == arg:
        return None
    return a.lower()

def configure_logging(argv, config):
    level = _logging.WARNING

    # Load logging info from config
    if config.get('verbose'):
        level = _logging.INFO
    if config.get('debug'):
        level = _logging.DEBUG
    logfile = config.get('log')

    # Load logging info from arguments
    # Also remove any arguments consumed so that the parser does not
    # have to explicitly ignore them.
    i = 0
    while i < len(argv):
        arg = _arg_name(argv[i])
        if arg in ('v', 'verbose'):
            level = min(_logging.INFO, level)
            argv.pop(i)
        elif arg in ('debug',):
            level = min(_logging.DEBUG, level)
            argv.pop(i)
        elif arg in ('log',):
            argv.pop(i)
            try:
                logfile = argv.pop(i)
            except IndexError:
                pass
        else:
            i += 1

    # Configure the console output handler
    stderr_handler = _logging.StreamHandler(sys.stderr)
    stderr_handler.formatter = _logging.Formatter('%(levelname)s: %(message)s')
    logger.level = stderr_handler.level = level
    logger.handlers.append(stderr_handler)

    if logfile:
        # Configure the handler that logs code to a text file
        log_handler = _logging.StreamHandler(open(logfile, 'w', encoding='utf-8'))
        log_handler.formatter = _logging.Formatter('[%(levelname)s:%(asctime)s] %(message)s')
        log_handler.level = level if level == _logging.DEBUG else _logging.INFO
        logger.handlers.append(log_handler)
