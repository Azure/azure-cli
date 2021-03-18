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
        type = values[1]
        
        if type.lower() == STATIC:
            if valuesLen < 3 or valuesLen > 4:
               raise CLIError('usage error: --delivery-attribute-mapping somename static VALUE [ISSECRET]')
            value = values[2]
            isSecret = False
            if valuesLen == 4:
                isSecret = bool(values[3])
            delivery_attribute_mapping = StaticDeliveryAttributeMapping(name=name,type=type,value=value,is_secret=isSecret)
        elif type.lower() == DYNAMIC:
            if valuesLen != 3:
                raise CLIError('usage error: --delivery-attribute-mapping somename dynamic SOURCEFIELD')
            sourceField = values[2]
            delivery_attribute_mapping = DynamicDeliveryAttributeMapping(name=name,type=type,source_field=sourceField)
        else:
            raise CLIError('usage error: --delivery-attribute-mapping NAME TYPE [SOURCEFIELD] [VALUE] [ISSECRET]')

        if namespace.delivery_attribute_mapping is None:
            namespace.delivery_attribute_mapping = []
        namespace.delivery_attribute_mapping.append(delivery_attribute_mapping)