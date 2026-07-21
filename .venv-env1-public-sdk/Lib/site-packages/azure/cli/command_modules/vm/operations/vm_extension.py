# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from azure.cli.core.aaz import AAZStrType
from ..aaz.latest.vm.extension import Show as _VMExtensionShow, Create as _VMExtensionCreate, List as _VMExtensionList

logger = get_logger(__name__)


class VMExtensionShow(_VMExtensionShow):

    class VirtualMachineExtensionsGet(_VMExtensionShow.VirtualMachineExtensionsGet):

        # Override to solve key conflict of _schema_on_200.properties.type when deserializing output
        @classmethod
        def _build_schema_on_200(cls):
            schema = super()._build_schema_on_200()

            del schema.properties._fields['type']
            schema.properties.type = AAZStrType(
                serialized_name="typePropertiesType",
            )
            return schema


class VMExtensionList(_VMExtensionList):

    class VirtualMachineExtensionsList(_VMExtensionList.VirtualMachineExtensionsList):

        # Override to solve key conflict of _schema_on_200.value.Element.properties.type when deserializing output
        @classmethod
        def _build_schema_on_200(cls):
            schema = super()._build_schema_on_200()

            del schema.value.Element.properties._fields['type']
            schema.value.Element.properties.type = AAZStrType(
                serialized_name="typePropertiesType",
            )
            return schema


class VMExtensionCreate(_VMExtensionCreate):

    class VirtualMachineExtensionsCreateOrUpdate(_VMExtensionCreate.VirtualMachineExtensionsCreateOrUpdate):

        # Override to solve key conflict of _schema_on_200.properties.type when deserializing output
        @classmethod
        def _build_schema_on_200_201(cls):
            schema = super()._build_schema_on_200_201()

            del schema.properties._fields['type']
            schema.properties.type = AAZStrType(
                serialized_name="typePropertiesType",
            )
            return schema
