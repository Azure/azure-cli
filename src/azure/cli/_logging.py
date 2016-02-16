import logging as _logging
import sys

_CODE_LEVEL = _logging.INFO + 1

class Logger(_logging.Logger):
    def __init__(self, name, level = _logging.NOTSET):
        super(Logger, self).__init__(name, level)

    def code(self, msg, *args):
        self._log(_CODE_LEVEL, msg, args)

logging = Logger('az', _logging.WARNING)

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
    # TODO: Configure logging handler to log messages to .py file
    # Thinking here:
    #   INFO messages as Python code
    #   DEBUG messages (if -v) as comments
    #   WARNING/ERROR messages as clearly marked comments
    
    # Currently we just use the default format
    level = _logging.WARNING
    if config.get('verbose'):
        level = _logging.INFO
    if config.get('debug'):
        level = _logging.DEBUG

    logfile = None
    i = 0
    while i < len(argv):
        arg = _arg_name(argv[i])
        if arg in ('v', 'verbose'):
            level = _logging.INFO
            argv.pop(i)
        elif arg in ('debug',):
            level = _logging.DEBUG
            argv.pop(i)
        elif arg in ('log',):
            argv.pop(i)
            try:
                logfile = argv.pop(i)
            except IndexError:
                pass
        else:
            i += 1
    logging.setLevel(_logging.INFO)

    stderr_handler = _logging.StreamHandler(sys.stderr)
    stderr_handler.formatter = _logging.Formatter('%(levelname)s: %(message)s')
    stderr_handler.level = level
    logging.handlers.append(stderr_handler)

    if logfile and logfile.lower().endswith('.py'):
        py_handler = _logging.StreamHandler(open(logfile, 'w', encoding='utf-8'))
        py_handler.formatter = PyFileFormatter()
        py_handler.level = level if level == _logging.DEBUG else _logging.INFO
        logging.handlers.append(py_handler)
    elif logfile:
        log_handler = _logging.StreamHandler(open(logfile, 'w', encoding='utf-8'))
        log_handler.formatter = _logging.Formatter('[%(levelname)s:%(asctime)s] %(message)s')
        log_handler.level = level if level == _logging.DEBUG else _logging.INFO
        logging.handlers.append(log_handler)