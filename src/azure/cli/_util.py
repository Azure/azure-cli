class CLIError(Exception):
    """Base class for exceptions that occur during
    normal operation of the application.
    Typically due to user error and can be resolved by the user.
    """
    pass

def normalize_newlines(str_to_normalize):
    return str_to_normalize.replace('\r\n', '\n')
