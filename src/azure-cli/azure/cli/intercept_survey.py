# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import sys
from azure.cli.core._config import GLOBAL_CONFIG_DIR

SURVEY_NOTE_NAME = 'az_survey.json'
GLOBAL_SURVEY_NOTE_PATH = os.path.join(GLOBAL_CONFIG_DIR, SURVEY_NOTE_NAME)

SURVEY_STYLE = '\x1b[0;38;2;255;255;255;48;2;0;120;212m'  # Default & Foreground #FFFFFF & Background #0078D4
SURVEY_LINK_STYLE = '\x1b[4;38;2;255;255;255;48;2;0;120;212m'  # Underline & Foreground #FFFFFF & Background #0078D4
NEW_LINE = '\x1b[1L'
ERASE_IN_LINE = '\x1b[0K'


def should_prompt(cli):
    if not cli.config.getboolean('core', 'survey_message', True):
        return False

    if sys.argv[1] == 'survey':
        return False

    return True


def prompt_survey_message(cli):
    try:
        if not should_prompt(cli):
            return

        # A workaround to enable ANSI CODE in Windows (https://stackoverflow.com/questions/12492810)
        if cli._should_init_colorama:
            os.system("")

        from azure.cli.core.style import Style, print_styled_text
        print_styled_text((SURVEY_STYLE, NEW_LINE))
        print_styled_text([
            (SURVEY_STYLE, "[Survey] Help us improve Azure CLI by sharing your experience. "
                           "This survey should take about 3 minutes. Run "),
            (SURVEY_LINK_STYLE, "az survey"),
            (SURVEY_STYLE, " to open in browser. Learn more at "),
            (SURVEY_LINK_STYLE, "https://go.microsoft.com/tbd"),
            (SURVEY_STYLE, ERASE_IN_LINE)
        ])
        print_styled_text((SURVEY_STYLE, NEW_LINE))
    except Exception as ex:
        raise ex

