# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
from knack.util import CLIError


def _get_api_url():
    return "https://cli-recommendation.azurewebsites.net/api/RecommendationService"


def _get_last_cmd():
    '''Get last executed command from local log files'''
    import os
    his_file_name = os.path.join(os.environ['HOME'], '.azure', 'hackthon_cmd_history.log')
    with open(his_file_name, "r") as f:
        lines = f.read().splitlines()
        return lines[-1]
    return ''


def _update_last_cmd(cmd):
    import os
    his_file_name = os.path.join(os.environ['HOME'], '.azure', 'hackthon_cmd_history.log')
    with open(his_file_name, "a") as f:
        f.write("{}\n".format(cmd))


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
    recommends = response.json()['data']

    return recommends


def _send_feedback(command, is_helpful):
    pass


def _read_int(msg, default_value=0):
    ret = input(msg)
    if ret == '' or not ret.isnumeric():
        ret = default_value
    else:
        ret = int(ret)
    return ret


def _give_recommends(recommends):
    for i in range(len(recommends)):
        rec = recommends[i]
        print("{}. user {}".format(i, rec['command']))
        print("Recommended reason: {}% {}".format(rec['ratio'], rec['reason']))


def handle_next(cmd):
    msg = '''
Please select the type of recommendation you need:
1. all: It will intelligently analyze the types of recommendation you need, and may recommend multiple types of content to you
2. solution: Only the solutions to problems when errors occur are recommend
3. command: Only the commands with high correlation with previously executed commands are recommend
4. resource: Only the resources related to previously created resources are recommended
5. senario: Only the E2E scenarios related to current usage scenarios are recommended
'''
    print(msg)
    option = _read_int("What kind of recommendation do you want? (RETURN is to set all): ", 1)
    last_cmd, last_param = _get_last_cmd()
    recommends = _get_recommend_from_api(last_cmd, last_param, option)
    if not recommends:
        raise CLIError("Failed to get recommend for '{}'.".format(last_cmd))
    _give_recommends(recommends)
    option = _read_int("Which one is helpful to you? (If none, please input 0) :")
    if option == 0:
        _send_feedback(cmd, False)
        return "recommend abort"

    feedback = input("Does it help for you? (y/n): ")
    doit = input("Do you want to do it now? (y/n): ")
    if doit not in ["y", "yes", "Y", "Yes", "YES"]:
        ret = {"result": "Thank you for your feedback"}
        return ret
    # execute select command
    option = option - 1
    nx_cmd = recommends[0]["command"]
    nx_param = recommends[0]["param"]
    print("az {}".format(nx_cmd))

    nx_params = [item[2:] for item in nx_param.split(',')]
    for param in nx_params:
        value = input("Please input {}: ".format(param))

    invocation = cmd.cli_ctx.invocation_cls(cli_ctx=cmd.cli_ctx,
                                            parser_cls=cmd.cli_ctx.parser_cls,
                                            commands_loader_cls=cmd.cli_ctx.commands_loader_cls,
                                            help_cls=cmd.cli_ctx.help_cls)
    args = [nx_cmd, nx_param]
    _update_last_cmd(nx_cmd)
    ret = invocation.execute(args)
    return ret
