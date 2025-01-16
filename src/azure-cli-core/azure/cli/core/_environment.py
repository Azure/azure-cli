# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


_ENV_AZ_INSTALLER = 'AZ_INSTALLER'
_ENV_AZ_BICEP_GLOBALIZATION_INVARIANT = 'AZ_BICEP_GLOBALIZATION_INVARIANT'


def get_config_dir():
    import os
    def sanitize(*d):
        return os.path.expanduser(os.path.expandvars(os.path.join(*d)))
    
    # Directory set in env has precedence
    if env := os.getenv('AZURE_CONFIG_DIR'):
        return sanitize(env)
    
    # Honor XDG variables
    if env := os.getenv('XDG_CONFIG_HOME'):
        return sanitize(env, 'azure')
    
    # Or the default fallover directory conform the XDG Base Directory Specification
    if os.path.isdir(sanitize('~', '.config')):
        return sanitize('~', '.config', 'azure')
    
    # If all others fail, return a dot-dir in the user's home directory.
    return sanitize('~', '.azure')
