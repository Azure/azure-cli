# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer

from azure.cli.command_modules.profile.custom import _load_subscriptions


@Completer
def get_subscription_id_list(cmd, prefix, namespace, **kwargs):  # pylint: disable=unused-argument
    subscriptions = _load_subscriptions(cmd.cli_ctx)
    result = []
    for subscription in subscriptions:
        result.append(subscription['id'])
        result.append(subscription['name'])
    return result
