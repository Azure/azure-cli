# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from collections import namedtuple
import hashlib
import random
import json
import re
import sys
import platform
import requests
import colorama  # pylint: disable=import-error


from azure.cli.core import telemetry as telemetry_core
from azure.cli.core import __version__ as core_version
from azure.cli.core.commands.constants import SURVEY_PROMPT
from packaging.version import parse
from knack.log import get_logger
logger = get_logger(__name__)

WAIT_MESSAGE = ['Finding examples...']

EXTENSION_NAME = 'find'


Example = namedtuple("Example", "title snippet")


def process_query(cli_term):
    if not cli_term:
        logger.error('Please provide a search term e.g. az find "vm"')
    else:
        print(random.choice(WAIT_MESSAGE), file=sys.stderr)
        response = call_aladdin_service(cli_term)

        if response.status_code != 200:
            logger.error('Unexpected Error: If it persists, please file a bug.')
        else:
            if (platform.system() == 'Windows' and should_enable_styling()):
                colorama.init(convert=True)
            has_pruned_answer = False
            answer_list = json.loads(response.content)
            if not answer_list:
                print("\nSorry I am not able to help with [" + cli_term + "]."
                      "\nTry typing the beginning of a command e.g. " + style_message('az vm') + ".", file=sys.stderr)
            else:
                if answer_list[0]['source'] == 'pruned':
                    has_pruned_answer = True
                    answer_list.pop(0)
                print("\nHere are the most common ways to use [" + cli_term + "]: \n", file=sys.stderr)

                for answer in answer_list:
                    cleaned_answer = clean_from_http_answer(answer)
                    print(style_message(cleaned_answer.title))
                    print(cleaned_answer.snippet + '\n')
                if has_pruned_answer:
                    print(style_message("More commands and examples are available in the latest version of the CLI. "
                                        "Please update for the best experience.\n"))
    from azure.cli.core.util import show_updates_available
    show_updates_available(new_line_after=True)
    print(SURVEY_PROMPT)


def get_generated_examples(cli_term):
    examples = []
    response = call_aladdin_service(cli_term)

    if response.status_code == 200:
        for answer in json.loads(response.content):
            examples.append(clean_from_http_answer(answer))

    return examples


def style_message(msg):
    if should_enable_styling():
        try:
            msg = colorama.Style.BRIGHT + msg + colorama.Style.RESET_ALL
        except KeyError:
            pass
    return msg


def should_enable_styling():
    try:
        # Style if tty stream is available
        if sys.stdout.isatty():
            return True
    except AttributeError:
        pass
    return False


def call_aladdin_service(query):
    version = str(parse(core_version))
    correlation_id = telemetry_core._session.correlation_id   # pylint: disable=protected-access
    subscription_id = telemetry_core._get_azure_subscription_id()  # pylint: disable=protected-access

    # Used for DDOS protection and rate limiting
    user_id = telemetry_core._get_installation_id()  # pylint: disable=protected-access
    hashed_user_id = hashlib.sha256(user_id.encode('utf-8')).hexdigest()

    context = {
        "versionNumber": version,
    }

    # Only pull in the contextual values if we have consent
    if telemetry_core.is_telemetry_enabled():
        context['correlationId'] = correlation_id

    if telemetry_core.is_telemetry_enabled() and subscription_id is not None:
        context['subscriptionId'] = subscription_id

    api_url = 'https://app.aladdin.microsoft.com/api/v1.0/examples'
    headers = {
        'Content-Type': 'application/json',
        'X-UserId': hashed_user_id
    }

    response = requests.get(
        api_url,
        params={
            'query': query,
            'clientType': 'AzureCli',
            'context': json.dumps(context)
        },
        headers=headers)

    return response


def clean_from_http_answer(http_answer):
    current_title = http_answer['title'].strip()
    current_snippet = http_answer['snippet'].strip()
    if current_title.startswith("az "):
        current_title, current_snippet = current_snippet, current_title
        current_title = current_title.split('\r\n')[0]
    elif '```azurecli\r\n' in current_snippet:
        start_index = current_snippet.index('```azurecli\r\n') + len('```azurecli\r\n')
        current_snippet = current_snippet[start_index:]
    current_snippet = current_snippet.replace('```', '').replace(current_title, '').strip()
    current_snippet = re.sub(r'\[.*\]', '', current_snippet).strip()
    return Example(current_title, current_snippet)
