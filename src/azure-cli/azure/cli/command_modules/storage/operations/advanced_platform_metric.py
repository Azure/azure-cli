# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..aaz.latest.storage.advanced_platform_metric import Update as _AdvancedPlatformMetricUpdate
from knack.log import get_logger

logger = get_logger(__name__)


class AdvancedPlatformMetricUpdate(_AdvancedPlatformMetricUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.advanced_platform_metrics_rule_type._required = False  # pylint: disable=protected-access
        return args_schema

    def pre_operations(self):
        args = self.ctx.args
        if not args.advanced_platform_metrics_rule_type:
            args.advanced_platform_metrics_rule_type = 'ContainerLevelCapacityMetrics'
        if args.rule_config_filter_type == 'AllContainersFilter':
            args.rule_config_filter_values = []
