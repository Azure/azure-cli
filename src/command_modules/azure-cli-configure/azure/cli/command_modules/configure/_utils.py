#---------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#---------------------------------------------------------------------------------------------

from six.moves import input, configparser #pylint: disable=redefined-builtin

import azure.cli.core._logging as _logging

logger = _logging.get_az_logger(__name__)

def prompt_y_n(msg, default=None):
    if default not in [None, 'y', 'n']:
        raise ValueError("Valid values for default are 'y', 'n' or None")
    y = 'Y' if default == 'y' else 'y'
    n = 'N' if default == 'n' else 'n'
    while True:
        ans = input('{} ({}/{}): '.format(msg, y, n))
        if ans.lower() == n.lower():
            return False
        if ans.lower() == y.lower():
            return True
        if default and not ans:
            return default == y.lower()

def prompt_choice_list(msg, a_list, default=1):
    '''Prompt user to select from a list of possible choices.
    :param str msg:A message displayed to the user before the choice list
    :param str a_list:The list of choices (list of strings or list of dicts with 'name' & 'desc')
    :param int default:The default option that should be chosen if user doesn't enter a choice
    :returns: The list index of the item chosen.
    '''
    options = '\n'.join([' [{}] {}{}'\
                        .format(i+1,
                                x['name'] if isinstance(x, dict) and 'name' in x else x,\
                                ' - '+x['desc'] if isinstance(x, dict) and 'desc' in x else '') \
                                for i, x in enumerate(a_list)])
    allowed_vals = list(range(1, len(a_list)+1))
    while True:
        try:
            ans = int(input('{}\n{}\nPlease enter a choice [{}]: '.format(msg, options, default)) \
                            or default)
            if ans in allowed_vals:
                # array index is 0-based, user input is 1-based
                return ans-1
            raise ValueError
        except ValueError:
            logger.warning('Valid values are %s', allowed_vals)

def get_default_from_config(config, section, option, choice_list, fallback=1):
    try:
        config_val = config.get(section, option)
        return [i for i, x in enumerate(choice_list) \
               if 'name' in x and x['name'] == config_val][0]+1
    except (IndexError, configparser.NoSectionError, configparser.NoOptionError):
        return fallback
