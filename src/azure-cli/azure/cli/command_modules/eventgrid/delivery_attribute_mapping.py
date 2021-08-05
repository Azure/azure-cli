# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import argparse
from knack.util import CLIError
from azure.mgmt.eventgrid.models import (
    StaticDeliveryAttributeMapping,
    DynamicDeliveryAttributeMapping
)

STATIC = "static"
DYNAMIC = "dynamic"


# pylint: disable=protected-access
# pylint: disable=too-few-public-methods
class AddDeliveryAttributeMapping(argparse._AppendAction):
    def __call__(self, parser, namespace, values, option_string=None):
        valuesLen = len(values)
        if valuesLen < 2:
            raise CLIError('usage error: --delivery-attribute-mapping NAME TYPE [SOURCEFIELD] [VALUE] [ISSECRET]')
        name = values[0]
        delivery_attribute_type = values[1]

        if delivery_attribute_type.lower() == STATIC:
            if valuesLen < 3 or valuesLen > 4:
                raise CLIError('usage error: --delivery-attribute-mapping <name> static <value> [<true/false>]')
            value = values[2]
            isSecret = False
            if valuesLen == 4:
                isSecret = bool(values[3])
            delivery_attribute_mapping = StaticDeliveryAttributeMapping(
                name=name,
                type=delivery_attribute_type,
                value=value,
                is_secret=isSecret)
        elif delivery_attribute_type.lower() == DYNAMIC:
            if valuesLen != 3:
                raise CLIError('usage error: --delivery-attribute-mapping <name> dynamic <value>')
            sourceField = values[2]
            delivery_attribute_mapping = DynamicDeliveryAttributeMapping(
                name=name,
                type=delivery_attribute_type,
                source_field=sourceField)
        else:
            raise CLIError('usage error: --delivery-attribute-mapping NAME TYPE [SOURCEFIELD] [VALUE] [ISSECRET]')

        if namespace.delivery_attribute_mapping is None:
            namespace.delivery_attribute_mapping = []
        namespace.delivery_attribute_mapping.append(delivery_attribute_mapping)
