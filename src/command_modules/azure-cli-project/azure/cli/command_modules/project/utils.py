# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import string
import random
import sys


def get_random_string(length=6):
    """
    Gets a random lowercase string made
    from ascii letters and digits
    """
    return ''.join(random.choice(string.ascii_lowercase + string.digits)
                   for _ in range(length))

def writeline(message):
    """
    Writes a message to stdout
    """
    sys.stdout.write(message + '\n')
