# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from __future__ import print_function
import sys

from knack.log import get_logger
from knack.prompting import prompt, NoTTYException
from knack.util import CLIError

from azure.cli.core.util import COMPONENT_PREFIX, get_installed_cli_distributions
from azure.cli.core.telemetry import set_feedback

logger = get_logger(__name__)

MSG_RATE = '\nHow likely is it you would recommend our Azure CLI to a friend or colleague? [0 to 10]: '
MSG_INTR = 'We appreciate your feedback! This survey is only two questions and should take less than a minute.'
MSG_BAD = '\nWhat changes would we have to make for you to give us a higher rating? '
MSG_GOOD = '\nWhat do we do really well? '
MSG_EMIL = '\nIf you would like to join our insiders program and receive tips, tricks, and early access to new ' \
           'features, let us know by leaving your email address (leave blank to skip): '
MSG_THNK = '\nThanks for your feedback!'


def _prompt_net_promoter_score():
    score = -1
    help_string = 'Please rate between 0 and 10'
    while score < 0 or score > 10:
        try:
            score = int(prompt(MSG_RATE, help_string=help_string))
        except ValueError:
            logger.warning(help_string)

    return score


def _get_version_info():
    installed_dists = get_installed_cli_distributions()

    component_version_info = sorted([{'name': dist.key.replace(COMPONENT_PREFIX, ''),
                                      'version': dist.version}
                                     for dist in installed_dists
                                     if dist.key.startswith(COMPONENT_PREFIX)],
                                    key=lambda x: x['name'])
    return str(component_version_info), sys.version


def handle_feedback():
    try:
        print(MSG_INTR)
        score = _prompt_net_promoter_score()
        if score == 10:
            suggestion = prompt(MSG_GOOD)
        else:
            suggestion = prompt(MSG_BAD)
        email_address = prompt(MSG_EMIL)
        set_feedback('[{}]{}[{}]'.format(score, suggestion, email_address))
        print(MSG_THNK)
    except NoTTYException:
        raise CLIError('This command is interactive and no tty available.')
    except (EOFError, KeyboardInterrupt):
        print()
