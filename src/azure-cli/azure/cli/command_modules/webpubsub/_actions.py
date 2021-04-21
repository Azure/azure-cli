# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

import argparse
from azure.mgmt.webpubsub.models import EventHandlerTemplate
from knack.log import get_logger
from azure.cli.core.azclierror import InvalidArgumentValueError

logger = get_logger(__name__)


# pylint: disable=protected-access, too-few-public-methods
class EventHandlerTemplateUpdateAction(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        logger.warning(self.dest)
        logger.warning(namespace)
        logger.warning(values)
        kwargs = {}
        for item in values:
            try:
                key, value = item.split('=', 1)
                kwargs[key.replace('-', '_')] = value
            except ValueError:
                raise InvalidArgumentValueError('usage error: {} KEY=VALUE [KEY=VALUE ...]'.format(option_string))
        logger.warning(kwargs)
        value = EventHandlerTemplate(**kwargs)
        super().__call__(parser, namespace, value, option_string)
