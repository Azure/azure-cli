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
    his_file_name = os.path.join(os.environ['HOME'], '.azure', 'recommendation', 'hackthon_cmd_history.log')
    with open(his_file_name, "r") as f:
        lines = f.read().splitlines()
        lines = [x for x in lines if x != 'next']
        return lines[-1]
    return ''


def _update_last_cmd(cmd):
    import os
    his_file_name = os.path.join(os.environ['HOME'], '.azure', 'recommendation', 'hackthon_cmd_history.log')
    with open(his_file_name, "a") as f:
        f.write("{}\n".format(cmd))


def _get_recommend_from_local(last_cmd, last_param, request_type, top_num=5, extra_data=None):
    import os
    mock_db = os.path.join(os.environ['HOME'], '.azure', 'recommendation', 'mock-db.json')
    with open(mock_db, 'r') as f:
        db = json.load(f)

    error_path = os.path.join(os.environ['HOME'], '.azure', 'recommendation','error')
    if last_cmd == 'notification-hub namespace create':
        if os.path.isfile(error_path):
            fix_error = True
            os.remove(error_path)
        else:
            open(error_path, 'a').close()
            fix_error = False
        


    for item in db['data']:
        if item['command'] == last_cmd:
            if last_cmd == 'notification-hub namespace create':
                if fix_error:
                    return item['nextCommand'][2:]
                else:
                    return item['nextCommand'][:2]
            return item['nextCommand']

    return []


def _get_recommend_from_api(last_cmd, last_param, request_type, top_num=5, extra_data=None):
    '''query next command from web api'''
    import requests
    url = _get_api_url()
    payload = {
        "command": last_cmd,
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
    print("")
    for i in range(len(recommends)):
        rec = recommends[i]
        print("{}. az {}".format(i + 1, rec['command']))
        print("Recommended reason: {}% {}".format(rec['ratio'] * 100, rec['reason']))


def handle_next(cmd):
    msg = '''
Please select the type of recommendation you need:
1. all: It will intelligently analyze the types of recommendation you need, and may recommend multiple types of command to you
2. solution: Only the solutions to problems when errors occur are recommend
3. command: Only the commands with high correlation with previously executed commands are recommend
4. resource: Only the resources related to previously created resources are recommended
5. senario: Only the E2E scenarios related to current usage scenarios are recommended
'''
    print(msg)
    option = _read_int("What kind of recommendation do you want? (RETURN is to set all): ", 1)
    last_cmd = _get_last_cmd()
    last_param = ''
    # recommends = _get_recommend_from_api(last_cmd, last_param, option)
    recommends = _get_recommend_from_local(last_cmd, last_param, option)
    if not recommends:
        raise CLIError("Failed to get recommend for '{}'.".format(last_cmd))
    _give_recommends(recommends)
    print()
    if len(recommends) > 1:
        option = _read_int("Which one is helpful to you? (If none, please input 0) :")
    else:
        option = input("Does it helpful to you? (y/n): ")
        if option in ["y", "yes", "Y", "Yes", "YES"]:
            option = 1
        else:
            option = 0
    if option == 0:
        _send_feedback(cmd, False)
        return "recommend abort"

    # print()
    # feedback = input("Does it help for you? (y/n): ")
    # execute select command
    option = option - 1
    nx_cmd = recommends[option]["command"]
    nx_param = recommends[option]["arguments"]
    print("Run: az {} {}".format(nx_cmd, ' '.join(nx_param)))
    print()
    doit = input("Do you want to run it now? (y/n): ")
    if doit not in ["y", "yes", "Y", "Yes", "YES"]:
        ret = {"result": "Thank you for your feedback"}
        return ret

    args = []
    args.extend(nx_cmd.split())
    for param in nx_param:
        value = input("Please input {}: ".format(param))
        args.append(param)
        args.append(value)

    # invocation = cmd.cli_ctx.invocation_cls(cli_ctx=cmd.cli_ctx,
    #                                         parser_cls=cmd.cli_ctx.parser_cls,
    #                                         commands_loader_cls=cmd.cli_ctx.commands_loader_cls,
    #                                         help_cls=cmd.cli_ctx.help_cls)
    # _update_last_cmd(nx_cmd)
    # ret = invocation.execute(args)
    ret = cmd.cli_ctx.invoke(args)
    return None
