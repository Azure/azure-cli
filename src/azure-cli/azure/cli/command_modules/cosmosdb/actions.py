# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse

from knack.log import get_logger
from knack.util import CLIError

from azure.mgmt.cosmosdb.models import (
    Location
)

logger = get_logger(__name__)


# pylint: disable=protected-access, too-few-public-methods
class CreateLocation(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        if namespace.locations is None:
            namespace._deprecated_location_format = False
            namespace.locations = []

        if any("regionname" in s.lower() for s in values):
            keys_found = set()
            _name = ""
            _failover = 0
            _is_zr = False
            for item in values:
                kvp = item.split('=', 1)
                _key = kvp[0].lower()
                if _key in keys_found:
                    # pylint: disable=line-too-long
                    raise CLIError('usage error: --locations [KEY=VALUE ...]. KEY {} provided multiple times'.format(_key))
                keys_found.add(_key)
                if _key == "regionname":
                    _name = kvp[1]
                elif _key == "failoverpriority":
                    _failover = int(kvp[1])
                elif _key == "iszoneredundant":
                    _is_zr = kvp[1].lower() == "true"
                else:
                    # pylint: disable=line-too-long
                    raise CLIError('usage error: --locations [KEY=VALUE ...]. KEY {} not supported. Valid keys are regionName, failoverPriority, and isZoneRedundant'.format(_key))
            namespace.locations.append(
                Location(location_name=_name,
                         failover_priority=_failover,
                         is_zone_redundant=_is_zr))
        else:
            # pylint: disable=line-too-long
            if not namespace._deprecated_location_format:
                logger.warning('The regionName=failoverPriority method of specifying locations is deprecated. Use --locations KEY=VALUE [KEY=VALUE ...] to specify the regionName, failoverPriority, and isZoneRedundant properties of the location. Multiple locations can be specified by including more than one --locations argument.')
            namespace._deprecated_location_format = True

            for item in values:
                comps = item.split('=', 1)
                namespace.locations.append(
                    Location(location_name=comps[0],
                             failover_priority=int(comps[1]),
                             is_zone_redundant=False))
