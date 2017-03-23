# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import string
import random
import sys
import os
from random_words import RandomWords


def get_random_registry_name():
    """
    Gets a random name for the Azure
    Container Registry
    """
    return get_random_string(only_letters=True)


def get_random_string(length=6, only_letters=False):
    """
    Gets a random lowercase string made
    from ascii letters and digits
    """
    random_string = ''
    if only_letters:
        random_string = ''.join(random.choice(string.ascii_lowercase)
                                for _ in range(length))
    else:
        random_string = ''.join(random.choice(string.ascii_lowercase + string.digits)
                                for _ in range(length))
    return random_string


def get_random_word():
    """
    Gets a random word
    """
    rw = RandomWords()
    return rw.random_word()


def writeline(message):
    """
    Writes a message to stdout
    """
    sys.stdout.write(message + '\n')


def get_public_ssh_key_contents(
        file_name=os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub')):
    """
    Gets the public SSH key file contents
    """
    contents = None
    with open(file_name) as ssh_file:
        contents = ssh_file.read()
    return contents
