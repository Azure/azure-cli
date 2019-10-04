# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from __future__ import print_function

import random
import json
import re
import sys
import platform
import requests
import colorama  # pylint: disable=import-error


from azure.cli.core import telemetry as telemetry_core
from azure.cli.core import __version__ as core_version
from pkg_resources import parse_version
from knack.log import get_logger
logger = get_logger(__name__)

WAIT_MESSAGE = ['Finding examples...']

EXTENSION_NAME = 'find'


def process_query(cli_term):
    if not cli_term:
        logger.error('Please provide a search term e.g. az find "vm"')
    else:
        response = call_aladdin_service(cli_term)

        print(random.choice(WAIT_MESSAGE), file=sys.stderr)
        response = call_aladdin_service(cli_term)

        if response.status_code != 200:
            logger.error('[?] Unexpected Error: [HTTP %s]: Content: %s', response.status_code, response.content)
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
                    current_title = answer['title'].strip()
                    current_snippet = answer['snippet'].strip()
                    if current_title.startswith("az "):
                        current_title, current_snippet = current_snippet, current_title
                        current_title = current_title.split('\r\n')[0]
                    elif '```azurecli\r\n' in current_snippet:
                        start_index = current_snippet.index('```azurecli\r\n') + len('```azurecli\r\n')
                        current_snippet = current_snippet[start_index:]
                    current_snippet = current_snippet.replace('```', '').replace(current_title, '').strip()
                    current_snippet = re.sub(r'\[.*\]', '', current_snippet).strip()
                    print(style_message(current_title))
                    print(current_snippet + '\n')
                if has_pruned_answer:
                    print(style_message("More commands and examples are available in the latest version of the CLI. "
                                        "Please update for the best experience.\n"))


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
    client_request_id = ''
    if telemetry_core._session.application:  # pylint: disable=protected-access
        client_request_id = telemetry_core._session.application.data['headers']['x-ms-client-request-id']  # pylint: disable=protected-access

    session_id = telemetry_core._session._get_base_properties()['Reserved.SessionId']  # pylint: disable=protected-access
    subscription_id = telemetry_core._get_azure_subscription_id()  # pylint: disable=protected-access
    client_request_id = client_request_id  # pylint: disable=protected-access
    installation_id = telemetry_core._get_installation_id()  # pylint: disable=protected-access
    version = str(parse_version(core_version))

    context = {
        "sessionId": session_id,
        "subscriptionId": subscription_id,
        "clientRequestId": client_request_id,
        "installationId": installation_id,
        "versionNumber": version
    }

    api_url = 'https://app.aladdin.microsoft.com/api/v1.0/examples'
    headers = {'Content-Type': 'application/json'}

    response = requests.get(
        api_url,
        params={
            'query': query,
            'clientType': 'AzureCli',
            'context': json.dumps(context)
        },
        headers=headers)

    return response
