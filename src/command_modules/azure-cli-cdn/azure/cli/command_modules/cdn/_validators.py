# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError


def validate_origin(namespace):
    def check_port_range(port, msg):
        if port is not None and not 1 <= port <= 65535:
            raise CLIError(msg.format(port))
    if namespace.origins:
        msg = "{0} port for origin named {1} is outside of range (1 - 65535)."
        for idx, origin in enumerate(namespace.origins):
            origin.name = "{}-{}".format(origin.name, idx)
            check_port_range(origin.http_port, msg.format('HTTP', origin.name))
            check_port_range(origin.https_port, msg.format('HTTPS', origin.name))
    return True
