# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import re

from knack.util import CLIError

ACCOUNT_NAME_MIN_LENGTH = 2
ACCOUNT_NAME_MAX_LENGTH = 64
ACCOUNT_NAME_REGEX = re.compile("^[a-zA-Z0-9][a-zA-Z0-9_.-]*$")


def validate_account_name(namespace):
    """ Validates account name."""
    account_name = namespace.account_name
    char_len = len(account_name)

    if not ACCOUNT_NAME_MIN_LENGTH <= char_len <= ACCOUNT_NAME_MAX_LENGTH:
        raise CLIError("Input account-name is invalid. Account name character length must be between 2 and 64.")
    if not re.match(ACCOUNT_NAME_REGEX, account_name):
        raise CLIError("Input account-name is invalid. Allowed regex: " + ACCOUNT_NAME_REGEX.pattern +
                       "\nFirst character must be alphanumeric." +
                       "\nSubsequent character(s) must be any combination of alphanumeric, underscore (_), " +
                       "period (.), or hyphen (-).")
