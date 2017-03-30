# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import random
import string
import sys
import threading
from time import sleep

import petname


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


def get_random_name(words=2, separator="-"):
    """
    Gets a random name
    """
    return petname.Generate(words, separator)


def writeline(message):
    """
    Writes a message to stdout on a newline
    """
    sys.stdout.write(message + '\n')


def write(message='.'):
    """
    Writes a message to stdout
    """
    sys.stdout.write(message)
    sys.stdout.flush()


def log(message, logger):
    """
    Writes a message to logger
    """
    logger.info('\n' + message)


def get_public_ssh_key_contents(
        file_name=os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub')):
    """
    Gets the public SSH key file contents
    """
    contents = None
    with open(file_name) as ssh_file:
        contents = ssh_file.read()
    return contents


class Process(object):

    __process_stop = False  # To stop the thread
    wait_time_sec = 15

    def __init__(self):
        self.__long_process_start()

    def __process_output(self, message='.'):
        while not self.__process_stop:
            write(message)
            sleep(self.wait_time_sec)

    def __long_process_start(self):
        self.__process_stop = False
        thread = threading.Thread(
            target=self.__process_output, args=(), kwargs={})
        thread.start()

    def process_stop(self):
        self.__process_stop = True
