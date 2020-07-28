# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from knack.util import CLIError


def _get_api_url():
    return "http://azure-cli.azurewebsites.net/orchestrators/recommendation"


def _get_last_cmd():
    '''Get last executed command from local log files'''
    return "vm create", "-s,-g"


def _get_recommend_from_api(last_cmd, last_param, request_type, top_num=5, extra_data=None):
    '''query next command from web api'''
    import requests
    url = _get_api_url()
    payload = {
        "command": last_cmd,
        "param": last_param,
        "extra_data": extra_data,
        "type": request_type,
        "top_num": top_num
    }
    response = requests.post(url, json.dumps(payload))
    if response.status_code != 200:
        raise CLIError("Failed to connect to '{}' with status code '{}' and reason '{}'".format(
            url, response.status_code, response.reason))
    recommends = response.content.decode("utf-8")["data"]

    return recommends


def _send_feedback():
    pass


def handle_next(cmd):
    option = int(input(
        "What kind of recommendation do you want? (1.operation 2.command 3.resource 4.service 5.mix): "))
    last_cmd, last_param = _get_last_cmd()
    recommends = _get_recommend_from_api(last_cmd, last_param, option)
    if not recommends:
        raise CLIError("Failed to get recommend for '{}'.".format(last_cmd))
    nx_cmd = recommends[0]["command"]
    nx_param = recommends[0]["param"]
    print("az {}".format(nx_cmd))
    feedback = input("Does it help for you? (y/n): ")
    doit = input("Do you want to do it now? (y/n): ")

    if doit not in ["y", "yes", "Y", "Yes", "YES"]:
        ret = {"result": "Thank you for your feedback"}
        return ret

    nx_params = [item[2:] for item in nx_param.split(',')]
    for param in nx_params:
        value = input("Please input {}: ".format(param))

    invocation = cmd.cli_ctx.invocation_cls(cli_ctx=cmd.cli_ctx,
                                            parser_cls=cmd.cli_ctx.parser_cls,
                                            commands_loader_cls=cmd.cli_ctx.commands_loader_cls,
                                            help_cls=cmd.cli_ctx.help_cls)
    args = ["version"]
    ret = invocation.execute(args)
    return ret
