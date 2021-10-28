# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands import DEFAULT_CACHE_TTL

OUTPUT_LIST = [
    {'name': 'json', 'desc': 'JSON formatted output that most closely matches API responses.'},
    {'name': 'jsonc',
     'desc': 'Colored JSON formatted output that most closely matches API responses.'},
    {'name': 'table', 'desc': 'Human-readable output format.'},
    {'name': 'tsv', 'desc': 'Tab- and Newline-delimited. Great for GREP, AWK, etc.'},
    {'name': 'yaml', 'desc': 'YAML formatted output. An alternative to JSON. Great for configuration files.'},
    {'name': 'yamlc', 'desc': 'Colored YAML formatted output. An alternative to JSON. Great for configuration files.'},
    {'name': 'none', 'desc': 'No output, except for errors and warnings.'}
]

MSG_INTRO = '\nWelcome to the Azure CLI! This command will guide you through logging in and ' \
            'setting some default values.\n'
MSG_CLOSING = '\nYou\'re all set! Here are some commands to try:\n' \
              ' $ az login\n' \
              ' $ az vm create --help\n' \
              ' $ az feedback\n'

WARNING_CLOUD_FORBID_TELEMETRY = '\nYour current cloud: %s does not allow data collection.' \
                                 ' Telemetry is disabled regardless of the configuration.'

MSG_GLOBAL_SETTINGS_LOCATION = 'Your settings can be found at {}'

MSG_HEADING_CURRENT_CONFIG_INFO = 'Your current configuration is as follows:'
MSG_HEADING_ENV_VARS = '\nEnvironment variables:'

MSG_PROMPT_MANAGE_GLOBAL = '\nDo you wish to change your settings?'
MSG_PROMPT_GLOBAL_OUTPUT = '\nWhat default output format would you like?'
MSG_PROMPT_TELEMETRY = '\nMicrosoft would like to collect anonymous Azure CLI usage data to ' \
                       'improve our CLI.  Participation is voluntary and when you choose to ' \
                       'participate, your device automatically sends information to Microsoft ' \
                       'about how you use Azure CLI.  To update your choice, run "az configure" ' \
                       'again.\nSelect y to enable data collection.'
MSG_PROMPT_FILE_LOGGING = '\nWould you like to enable logging to file?'

MSG_PROMPT_CACHE_TTL = '\nCLI object cache time-to-live (TTL) in minutes [Default: {}]: '.format(DEFAULT_CACHE_TTL)
