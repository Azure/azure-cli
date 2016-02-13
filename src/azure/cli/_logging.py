import logging

def configure_logging(argv, config):
    # TODO: Configure logging handler to log messages to .py file
    # Thinking here:
    #   INFO messages as Python code
    #   DEBUG messages (if -v) as comments
    #   WARNING/ERROR messages as clearly marked comments
    
    # Currently we just use the default format
    level = logging.WARNING
    if '-v' in argv or '--verbose' in argv or config.get('verbose'):
        level = logging.INFO
    
    if '--debug' in argv or config.get('debug'):
        level = logging.DEBUG
    
    logging.basicConfig(level=level)
