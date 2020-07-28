# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.util import CLIError
import subprocess


def _get_last_cmd():
    '''Get last executed command from local log files'''
    pass


def _get_recommend_from_api(last_cmd, last_param):
    '''query next command from web api'''
    nx_cmd = "role assignment create"
    nx_param = "--role,--assignee,--scope"
    return nx_cmd, nx_param


def _send_feedback():
    pass


def handle_next(cmd):
    option = int(input(
        "What kind of recommendation do you want? (1.operation 2.command 3.resource 4.service 5.mix): "))
    nx_cmd, nx_param = _get_recommend_from_api("", "")
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
    ret =  invocation.execute(args)
    return ret

