import logging

# These arguments will be removed
STRIP_ARGS = frozenset([
    '-v',
    '--verbose',
    '--debug',
])

def configure_logging(argv):
    # TODO: Configure logging handler to log messages to .py file
    # Thinking here:
    #   INFO messages as Python code
    #   DEBUG messages (if -v) as comments
    #   WARNING/ERROR messages as clearly marked comments
    
    # Currently we just use the default format
    level = logging.WARNING
    if '-v' in argv or '--verbose' in argv:
        level = logging.INFO
    if '--debug' in argv:
        level = logging.DEBUG
    
    logging.basicConfig(level=level)
    
    return [a for a in argv if a not in STRIP_ARGS]