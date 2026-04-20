# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from ..aaz.latest.storage.advanced_platform_metric import Update as _AdvancedPlatformMetricUpdate
from knack.log import get_logger

logger = get_logger(__name__)

class AdvancedPlatformMetricUpdate(_AdvancedPlatformMetricUpdate):
    def pre_operations(self):
        args = self.ctx.args
        if args.rule_config_filter_type == 'AllContainersFilter':
            args.rule_config_filter_values = []
