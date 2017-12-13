# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.decorators import Completer

from ._client_factory import iot_hub_service_factory
from .custom import iot_device_list


@Completer
def get_device_id_completion_list(cmd, prefix, namespace):  # pylint: disable=unused-argument
    client = iot_hub_service_factory(cmd.cli_ctx)
    return [d.device_id for d in iot_device_list(client, namespace.hub_name, top=100)] if namespace.hub_name else []
