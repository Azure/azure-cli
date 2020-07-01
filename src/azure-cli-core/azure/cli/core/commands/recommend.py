
import argparse
from collections import OrderedDict
import copy
import json
import re
from six import string_types

from azure.cli.core import AzCommandsLoader, EXCLUDED_PARAMS
from azure.cli.core.commands import LongRunningOperation, _is_poller, cached_get, cached_put
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.commands.validators import IterateValue
from azure.cli.core.util import (
    shell_safe_json_parse, augment_no_wait_handler_args, get_command_type_kwarg, find_child_item)
from azure.cli.core.profiles import ResourceType, get_sdk

from knack.arguments import CLICommandArgument, ignore_type
from knack.introspection import extract_args_from_signature, extract_full_summary_from_signature
from knack.log import get_logger
from knack.util import todict, CLIError
from knack import events

logger = get_logger(__name__)


def register_global_query_recommend(cli_ctx):
    def add_query_recommend_parameter(_, **kwargs):
        recommend_dest = '_query_recommend'

        class QueryRecommendAction(argparse.Action):  # pylint:disable=too-few-public-methods

            def __call__(self, parser, namespace, value, option_string=None):
                if value != False:
                    setattr(namespace, recommend_dest, True)
                    cmd = getattr(namespace, 'cmd', None) or getattr(
                        namespace, '_cmd', None)
                    cmd.cli_ctx.data[recommend_dest] = True
                # from azure.cli.core._profile import Profile
                # profile = Profile(cli_ctx=namespace._cmd.cli_ctx)  # pylint: disable=protected-access
                # subscriptions_list = profile.load_cached_subscriptions()
                # sub_id = None
                # for sub in subscriptions_list:
                #     match_val = value.lower()
                #     if sub['id'].lower() == match_val or sub['name'].lower() == match_val:
                #         sub_id = sub['id']
                #         break
                # if not sub_id:
                #     logger.warning("Subscription '%s' not recognized.", value)
                #     sub_id = value

        commands_loader = kwargs['commands_loader']
        cmd_tbl = commands_loader.command_table

        for _, cmd in cmd_tbl.items():
            cmd.arguments[recommend_dest] = CLICommandArgument(
                '_query_recommend',
                options_list='--query-recommend',
                nargs='?',
                action=QueryRecommendAction,
                help='Generate query recommend for you.',
                is_preview=True

            )
        # cmd.add_argument('_query_recommend', '--query-recommend', **default_sub_kwargs)
        # cmd.add_argument('_query_recommend', '--query-recommend', arg_group='Global',
        #                  help='Generate recommend for you', action='store_true')

    def analyze_output(cli, event_data):
        pass

    cli_ctx.register_event(
        events.EVENT_INVOKER_POST_CMD_TBL_CREATE, add_query_recommend_parameter)
    cli_ctx.register_event(
        events.EVENT_INVOKER_TRANSFORM_RESULT, analyze_output)


def parse_dict(data):
    all_keys = list(data.keys())
    help_str = 'You can use --query \"{}\" to query {} value. Available values are:{}'.format(
        all_keys[0], all_keys[0], all_keys
    )
    return help_str


def parse_list(data):
    help_str = []
    for item in data:
        help_str.append(parse_dict(item))
    return '\n'.join(help_str)


def parse_output(data):
    help_str = "Output format is not supported"
    if isinstance(data, dict):
        help_str = parse_dict(data)
    elif isinstance(data, list):
        help_str = parse_list(data)
    else:
        logger.warning("Ootput format is not supported")
    return help_str
