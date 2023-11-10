# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import shutil
import requests

from azure.cli.core.style import Style, print_styled_text

_DEEPPROMPT_ENDPOINT = "https://data-ai-dev.microsoft.com/deepprompt/api/v1"
_DEEPPROMPT_APP = "7d78b7a3-e228-4b85-8fcf-5633fb326beb"
_AAD_TENANT = "72f988bf-86f1-41af-91ab-2d7cd011db47"
_SCOPES = [f"{_DEEPPROMPT_APP}/.default"]
_TIMEOUT = 180

_cached_token_session: tuple = ()

def request_error_assistance(command: str|None=None, error: str|None=None, cli_ctx=None) -> dict:
    if _error_enabled(cli_ctx):
        print("Generating error assistance. This may take a few seconds.")

        if not command:
            print("command cannot be empty")

        from azure.cli.core.azclierror import AuthenticationError
        try:
            global _cached_token_session
            if len(_cached_token_session) == 0:
                _cached_token_session = _refresh_cached_token_session(cli_ctx)

            retry_count: int = 5
            current_retry: int = 0

            while len(_cached_token_session) > 0 and current_retry < retry_count:
                (deepprompt_token, session_id) = _cached_token_session
                response = _send_query(deepprompt_token, session_id, command, error)

                if response.status_code == requests.codes.ok:
                    response_body = json.loads(response.json()["response_text"])
                    return response_body
                elif (response.status_code == requests.codes.unauthorized or response.status_code == requests.codes.forbidden):
                    _cached_token_session = _refresh_cached_token_session(cli_ctx)
                    current_retry = current_retry + 1
                    continue
                else:
                    print(f"Failed to get the response: {response.status_code}.")
                    break
        except AuthenticationError:
            print("Failed to authenticate to the service.")
        except Exception as e:
            print(f"Got an exception {e}")

    return {}


def print_error_assistance(response) -> None:
    if response:
        _print_line()

        explanation = response["Explanation"]

        if explanation:
            print_styled_text([(Style.ERROR, "Issue: ")])
            print(explanation)

        suggested_command = _validate_command(response["Suggestion"])

        if suggested_command:
            print_styled_text([(Style.ACTION, "Suggestion: ")])
            print(suggested_command)

        note = response["Note"]

        if note:
            print_styled_text([(Style.PRIMARY, "Note: ")])
            print(note)

        _print_line()


def _validate_command(command_response):
    # Incorporate syntax validation here
    # if command syntax is correct:
    return command_response
# else:
    # return "No command available."


def _print_line():
    console_width = shutil.get_terminal_size().columns
    dashed_line = "-" * console_width

    print_styled_text([(Style.IMPORTANT, dashed_line)])


def _error_enabled(cli_ctx) -> bool:
    return cli_ctx and (cli_ctx.config.getboolean("core", "error_assistance", fallback=False) or
                       cli_ctx.config.getboolean("interactive", "error_assistance", fallback=False))


def _exchange(aad_token: str) -> dict:
    return requests.post(
            url=f"{_DEEPPROMPT_ENDPOINT}/exchange",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                },
            json={
                "token": aad_token,
                "provider": "microsoft",
                },
            timeout=_TIMEOUT).json()

def _create_session(access_token: str) -> str:
    return requests.post(
            url=f"{_DEEPPROMPT_ENDPOINT}/create_session",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
                }).json()['session_id']

def _send_query(access_token: str, session_id: str, command: str|None, error: str|None) -> requests.Response:
    return requests.post(
            url=f"{_DEEPPROMPT_ENDPOINT}/query",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {access_token}",
                "DeepPrompt-Session-ID": session_id,
                },
            json={
                "query": "Query errors and corrected command for Azure CLI",
                "intent": "azure_error_recovery",
                "context": {
                    "command": command,
                    "error": error,
                    "language": "azurecli",
                    }
                })


def _refresh_cached_token_session(cli_ctx) -> tuple:
    from azure.cli.core._profile import Profile
    profile = Profile(cli_ctx=cli_ctx)
    aad_token = profile.get_raw_token(scopes=_SCOPES, tenant=_AAD_TENANT)[0][1]
    exchanged_token = _exchange(aad_token)
    session_id = exchanged_token["session_id"]
    deepprompt_token = exchanged_token["access_token"]

    return (deepprompt_token, session_id)
