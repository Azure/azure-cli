import logging as _logging
import sys

__all__ = ['logging', 'configure_logging']

logging = _logging.Logger('az', _logging.WARNING)

class PyFileFormatter(_logging.Formatter):
    def __init__(self):
        super(PyFileFormatter, self).__init__('# %(levelname)s: %(message)s')
        self.info_style = _logging.PercentStyle('%(message)s')

    def format(self, record):
        assert isinstance(record, _logging.LogRecord)
        if record.levelno == _CODE_LEVEL:
            return record.getMessage()
        return super(PyFileFormatter, self).format(record)

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
    logging.level = stderr_handler.level = level
    logging.handlers.append(stderr_handler)

    if logfile and logfile.lower().endswith('.py'):
        # Configure a handler that logs code to a Python script
        py_handler = _logging.StreamHandler(open(logfile, 'w', encoding='utf-8'))
        py_handler.formatter = PyFileFormatter()
        py_handler.level = level if level == _logging.DEBUG else _logging.INFO
        logging.handlers.append(py_handler)
    elif logfile:
        # Configure the handler that logs code to a text file
        log_handler = _logging.StreamHandler(open(logfile, 'w', encoding='utf-8'))
        log_handler.formatter = _logging.Formatter('[%(levelname)s:%(asctime)s] %(message)s')
        log_handler.level = level if level == _logging.DEBUG else _logging.INFO
        logging.handlers.append(log_handler)
