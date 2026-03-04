# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=line-too-long, protected-access, too-few-public-methods

from azure.cli.core.aaz import has_value
from azure.cli.command_modules.network.aaz.latest.network.lb.probe._update import Update as _LBProbeUpdate
from knack.log import get_logger

logger = get_logger(__name__)


class LBProbeUpdate(_LBProbeUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.port._nullable = False
        args_schema.protocol._nullable = False
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if has_value(args.number_of_probes):
            logger.warning(
                "The property \"numberOfProbes\" is not respected. Load Balancer health probes will probe up or down "
                "immediately after one probe regardless of the property's configured value. To control the number of "
                "successful or failed consecutive probes necessary to mark backend instances as healthy or unhealthy, "
                "please leverage the property \"probeThreshold\" instead."
            )
        if has_value(args.request_path) and args.request_path == "":
            args.request_path = None
