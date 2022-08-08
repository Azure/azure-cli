# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
import json
from datetime import datetime, timedelta
from azure.cli.core._config import GLOBAL_CONFIG_DIR
from azure.cli.core.style import windows_enable_vt_mode, print_styled_text
from knack.log import get_logger

logger = get_logger(__name__)

SURVEY_NOTE_NAME = 'az_survey.json'
GLOBAL_SURVEY_NOTE_PATH = os.path.join(GLOBAL_CONFIG_DIR, SURVEY_NOTE_NAME)

EXPERIENCE_PERIOD_IN_DAYS = 1
PROMPT_INTERVAL_IN_DAYS = 180

SURVEY_STYLE = '\x1b[0;38;2;255;255;255;48;2;0;120;212m'  # Default & Foreground #FFFFFF & Background #0078D4
SURVEY_BOLD_STYLE = '\x1b[1;38;2;255;255;255;48;2;0;120;212m'  # Underline & Foreground #FFFFFF & Background #0078D4
NEW_LINE = '\x1b[1L'
ERASE_IN_LINE = '\x1b[0K'


def should_prompt(cli):
    if not cli.config.getboolean('core', 'survey_message', True):
        return False

    if sys.argv[1] == 'survey':
        return False

    if not os.path.isfile(GLOBAL_SURVEY_NOTE_PATH):
        import uuid
        from azure.cli.core._profile import Profile

        # If the survey note file doesn't exist, then it should be the first time for cx to run CLI
        # We should let cx try CLI for some days(EXPERIENCE_PERIOD_IN_DAYS) and then prompt the survey message
        # We don't want to get the survey feedback on the same day, so we evenly distribute cx over 128 days
        # using their installationId
        installation_id = Profile(cli_ctx=cli).get_installation_id()
        prompt_period = EXPERIENCE_PERIOD_IN_DAYS + (uuid.UUID(installation_id).int & 127)
        next_prompt_time = datetime.utcnow() + timedelta(days=prompt_period)
        survey_note = {
            'last_prompt_time': '',
            'next_prompt_time': next_prompt_time.strftime('%Y-%m-%dT%H:%M:%S')
        }
        with open(GLOBAL_SURVEY_NOTE_PATH, 'w') as f:
            json.dump(survey_note, f)
        return False

    with open(GLOBAL_SURVEY_NOTE_PATH, 'r') as f:
        survey_note = json.load(f)
        next_prompt_time = datetime.strptime(survey_note['next_prompt_time'], '%Y-%m-%dT%H:%M:%S')
        if datetime.utcnow() < next_prompt_time:
            return False

    return True


def print_and_log(styled=True):
    if not styled:
        print("[Survey] Help us improve Azure CLI by sharing your experience. "
              "This survey should take about 3 minutes. Run 'az survey' to open in browser. "
              "Learn more at https://go.microsoft.com/fwlink/?linkid=2203309")
    else:
        print_styled_text((SURVEY_STYLE, NEW_LINE))
        print_styled_text([
            (SURVEY_STYLE, "[Survey] Help us improve Azure CLI by sharing your experience. "
                           "This survey should take about 3 minutes. Run 'az survey' to open in browser. "
                           "Learn more at https://go.microsoft.com/fwlink/?linkid=2203309"),
            (SURVEY_STYLE, ERASE_IN_LINE)
        ])
        print_styled_text((SURVEY_STYLE, NEW_LINE))

    next_prompt_time = datetime.utcnow() + timedelta(days=PROMPT_INTERVAL_IN_DAYS)
    survey_note = {
        'last_prompt_time': datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S'),
        'next_prompt_time': next_prompt_time.strftime('%Y-%m-%dT%H:%M:%S')
    }
    with open(GLOBAL_SURVEY_NOTE_PATH, 'w') as f:
        json.dump(survey_note, f)


def prompt_survey_message(cli):
    if not should_prompt(cli):
        return

    # If CLI enables colorama, which means it's running in windows with legacy terminal
    # we should enable VT mode first to print styled text using ANSI Escape Sequences
    if cli._should_init_colorama:
        try:
            windows_enable_vt_mode()
        except Exception as ex:  # pylint: disable=broad-except
            logger.debug("Failed to enable vt mode for windows. %s", str(ex))
            print_and_log(styled=False)

    print_and_log(styled=True)
