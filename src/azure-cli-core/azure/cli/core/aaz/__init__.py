# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=unused-import

""" AAZ is short for Atomic Azure CLI, which is an atomic command layer of azure cli.
The command in atomic layer is called atomic command, mapping to an operation of azure resource.
Atomic commands can be generated from rest api by using aaz-dev tool.
"""

from ._arg import AAZArgumentsSchema, AAZArgEnum, AAZStrArg, AAZIntArg, AAZObjectArg, AAZDictArg, \
    AAZFreeFormDictArg, AAZFloatArg, AAZBaseArg, AAZBoolArg, AAZListArg, AAZResourceGroupNameArg, \
    AAZResourceLocationArg, AAZResourceIdArg, AAZSubscriptionIdArg, AAZUuidArg, AAZDateArg, AAZTimeArg, \
    AAZDateTimeArg, AAZDurationArg, AAZFileArg, AAZPasswordArg, AAZPaginationTokenArg, AAZPaginationLimitArg, \
    AAZAnyTypeArg
from ._arg_fmt import AAZStrArgFormat, AAZIntArgFormat, AAZFloatArgFormat, AAZBoolArgFormat, AAZObjectArgFormat, \
    AAZDictArgFormat, AAZFreeFormDictArgFormat, AAZListArgFormat, AAZResourceLocationArgFormat, \
    AAZResourceIdArgFormat, AAZSubscriptionIdArgFormat, AAZUuidFormat, AAZDateFormat, AAZTimeFormat, \
    AAZDateTimeFormat, AAZDurationFormat, AAZFileArgTextFormat, AAZFileArgBase64EncodeFormat, AAZFileArgFormat, \
    AAZPaginationTokenArgFormat
from ._base import has_value, AAZValuePatch, AAZUndefined
from ._command import AAZCommand, AAZWaitCommand, AAZCommandGroup, \
    register_callback, register_command, register_command_group, load_aaz_command_table, link_helper
from ._field_type import AAZIntType, AAZFloatType, AAZStrType, AAZBoolType, AAZDictType, AAZFreeFormDictType, \
    AAZListType, AAZObjectType, AAZIdentityObjectType, AAZAnyType
from ._operation import AAZHttpOperation, AAZJsonInstanceUpdateOperation, AAZGenericInstanceUpdateOperation, \
    AAZJsonInstanceDeleteOperation, AAZJsonInstanceCreateOperation
from ._prompt import AAZPromptInput, AAZPromptPasswordInput
from ._selector import AAZJsonSelector
from ._client import AAZBaseClient, AAZClientConfiguration, register_client, CloudNameEnum
