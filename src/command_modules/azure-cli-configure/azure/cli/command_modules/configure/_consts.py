# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

OUTPUT_LIST = [
    {'name': 'json', 'desc': 'JSON formatted output that most closely matches API responses'},
    {'name': 'jsonc',
     'desc': 'Colored JSON formatted output that most closely matches API responses'},
    {'name': 'table', 'desc': 'Human-readable output format'},
    {'name': 'tsv', 'desc': 'Tab and Newline delimited, great for GREP, AWK, etc.'}
]

LOGIN_METHOD_LIST = [
    'Device code authentication, we will provide a code you enter into a web page and log into',
    "Username and password (MFA enforced accounts or MSA accounts such as live-id not supported)",
    'Service Principal with secret',
    'Skip this step (login is available with the \'az login\' command)'
]

MSG_INTRO = '\nWelcome to the Azure CLI! This command will guide you through logging in and ' \
            'setting some default values.\n'
MSG_CLOSING = '\nYou\'re all set! Here are some commands to try:\n' \
              ' $ az login\n' \
              ' $ az vm create --help\n' \
              ' $ az feedback\n'

MSG_GLOBAL_SETTINGS_LOCATION = 'Your settings can be found at {}'

MSG_HEADING_CURRENT_CONFIG_INFO = 'Your current configuration is as follows:'
MSG_HEADING_ENV_VARS = '\nEnvironment variables:'

MSG_PROMPT_MANAGE_GLOBAL = '\nDo you wish to change your settings?'
MSG_PROMPT_GLOBAL_OUTPUT = '\nWhat default output format would you like?'
MSG_PROMPT_LOGIN = '\nHow would you like to log in to access your subscriptions?'
MSG_PROMPT_TELEMETRY = '\nMicrosoft would like to collect anonymous Azure CLI usage data to ' \
                       'improve our CLI.  Participation is voluntary and when you choose to ' \
                       'participate, your device automatically sends information to Microsoft ' \
                       'about how you use Azure CLI.  To update your choice, run "az configure" ' \
                       'again.\nSelect y to enable data collection.'
MSG_PROMPT_FILE_LOGGING = '\nWould you like to enable logging to file?'
