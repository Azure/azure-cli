import getpass
import logging
from azure.cli.main import RC

COMMAND_NAME = 'login'
COMMAND_HELP = 'helps you log in'

def add_commands(parser):
    parser.add_argument('--user', '-u', metavar='USERNAME')

# Define the execute method for when the 'login' command is used
def execute(args):
    logging.info(vars(args))
