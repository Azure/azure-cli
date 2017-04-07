# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import random
import string
import sys
import threading
from subprocess import PIPE, CalledProcessError, Popen
from time import sleep

import azure.cli.core.azlogging as azlogging  # pylint: disable=invalid-name
from azure.cli.core._util import CLIError

logger = azlogging.get_az_logger(__name__)  # pylint: disable=invalid-name
left = [
    "admiring",
    "adoring",
    "agitated",
    "amazing",
    "angry",
    "awesome",
    "backstabbing",
    "berserk",
    "big",
    "boring",
    "clever",
    "cocky",
    "compassionate",
    "condescending",
    "cranky",
    "desperate",
    "determined",
    "distracted",
    "dreamy",
    "drunk",
    "ecstatic",
    "elated",
    "elegant",
    "evil",
    "fervent",
    "focused",
    "furious",
    "gigantic",
    "gloomy",
    "goofy",
    "grave",
    "happy",
    "high",
    "hopeful",
    "hungry",
    "insane",
    "jolly",
    "jovial",
    "kickass",
    "lonely",
    "loving",
    "mad",
    "modest",
    "naughty",
    "nostalgic",
    "pensive",
    "prickly",
    "reverent",
    "romantic",
    "sad",
    "serene",
    "sharp",
    "sick",
    "silly",
    "sleepy",
    "small",
    "stoic",
    "stupefied",
    "suspicious",
    "tender",
    "thirsty",
    "tiny",
    "trusting",
]

right = [
    "albattani",
    "allen",
    "almeida",
    "archimedes",
    "ardinghelli",
    "aryabhata",
    "austin",
    "babbage",
    "banach",
    "bardeen",
    "bartik",
    "bell",
    "bhabha",
    "bhaskara",
    "blackwell",
    "bohr",
    "booth",
    "borg",
    "bose",
    "boyd",
    "brahmagupta",
    "brattain",
    "brown",
    "carson",
    "chandrasekhar",
    "colden",
    "cori",
    "cray",
    "curie",
    "darwin",
    "davinci",
    "dijkstra",
    "dubinsky",
    "easley",
    "einstein",
    "elion",
    "engelbart",
    "euclid",
    "euler",
    "fermat",
    "fermi",
    "feynman",
    "franklin",
    "galileo",
    "gates",
    "goldberg",
    "goldstine",
    "goodall",
    "hamilton",
    "hawking",
    "heisenberg",
    "hodgkin",
    "hoover",
    "hopper",
    "hugle",
    "hypatia",
    "jang",
    "jennings",
    "jepsen",
    "joliot",
    "jones",
    "kalam",
    "kare",
    "keller",
    "khorana",
    "kilby",
    "kirch",
    "knuth",
    "kowalevski",
    "lalande",
    "lamarr",
    "leakey",
    "leavitt",
    "lichterman",
    "liskov",
    "lovelace",
    "lumiere",
    "mahavira",
    "mayer",
    "mccarthy",
    "mcclintock",
    "mclean",
    "mcnulty",
    "meitner",
    "meninsky",
    "mestorf",
    "mirzakhani",
    "morse",
    "newton",
    "nobel",
    "noether",
    "northcutt",
    "noyce",
    "panini",
    "pare",
    "pasteur",
    "payne",
    "perlman",
    "pike",
    "poincare",
    "poitras",
    "ptolemy",
    "raman",
    "ramanujan",
    "ride",
    "ritchie",
    "roentgen",
    "rosalind",
    "saha",
    "sammet",
    "shaw",
    "shockley",
    "sinoussi",
    "snyder",
    "spence",
    "stallman",
    "swanson",
    "swartz",
    "swirles",
    "tesla",
    "thompson",
    "torvalds",
    "turing",
    "varahamihira",
    "visvesvaraya",
    "wescoff",
    "williams",
    "wilson",
    "wing",
    "wozniak",
    "wright",
    "yalow",
    "yonath",
]


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


def get_random_project_name(separator="-"):
    """
    Gets a random name
    """
    return '{}{}{}'.format(random.choice(left), separator, random.choice(right))


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


def get_public_ssh_key_contents(
        file_name=os.path.join(os.path.expanduser('~'), '.ssh', 'id_rsa.pub')):
    """
    Gets the public SSH key file contents
    """
    contents = None
    with open(file_name) as ssh_file:
        contents = ssh_file.read()
    return contents


def get_remote_host(dns_prefix, location):
    """
    Provides a remote host according to the passed dns_prefix and location.
    """
    return '{}.{}.cloudapp.azure.com'.format(dns_prefix, location)


def execute_command(command, throw=False, tries=1):
    """
    Executes a shell command on a local machine
    """
    return_code = 1
    retry = 0
    while retry < tries:
        with Popen(command, shell=True, stdout=PIPE, stderr=PIPE, bufsize=1, universal_newlines=True) as process:
            for line in process.stdout:
                logger.info('\n' + line)
            if throw:
                for err in process.stderr:
                    logger.debug(err)
            # Wait for the process to finish to get the return code
            return_code = process.wait()
            if throw:
                raise CLIError(CalledProcessError(
                    return_code, command))
        if return_code == 0:
            break

        sleep(2)
        retry = retry + 1

    return return_code


class Process(object):
    """
    Process object runs a thread in the backgroud to print the
    status of an execution for which the output is not displayed to stdout.
    It prints '.' to stdout till the process is runnin.
    """

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
