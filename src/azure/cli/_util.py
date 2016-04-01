import os

AZURE_CLI_UPDATE_CHECK_USE_PRIVATE = "AZURE_CLI_UPDATE_CHECK_USE_PRIVATE"

def should_use_private_pypi():
    return bool(os.environ.get(AZURE_CLI_UPDATE_CHECK_USE_PRIVATE))

def normalize_newlines(str_to_normalize):
    return str_to_normalize.replace('\r\n', '\n')
