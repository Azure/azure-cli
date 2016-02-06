import os

try:
    import configparser
except ImportError:
    import ConfigParser as configparser

_loaded_config = None
def get_config():
    global _loaded_config
    if _loaded_config is None:
        cfg = configparser.RawConfigParser()
        cfg.read(os.path.expanduser('~/azure.ini'))
        _loaded_config = cfg
    return _loaded_config
