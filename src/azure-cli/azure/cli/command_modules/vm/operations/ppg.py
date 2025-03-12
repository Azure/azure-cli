# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from azure.cli.core.azclierror import RequiredArgumentMissingError
from azure.cli.core.aaz import has_value
from ..aaz.latest.ppg import Show as _PPGShow, Create as _PPGCreate, Update as _PPGUpdate

logger = get_logger(__name__)


class PPGShow(_PPGShow):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        from azure.cli.core.aaz import AAZArgEnum
        args_schema.include_colocation_status._blank = "True"
        args_schema.include_colocation_status.enum = AAZArgEnum({"True": "True", "False": "False"})

        return args_schema


class PPGCreate(_PPGCreate):
    def pre_operations(self):
        args = self.ctx.args

        # The availability zone can be provided only when an intent is provided
        if has_value(args.zone) and not has_value(args.intent_vm_sizes):
            raise RequiredArgumentMissingError('The --zone can be provided only when an intent is provided. '
                                               'Please use parameter --intent-vm-sizes to specify possible sizes of '
                                               'virtual machines that can be created in the proximity placement group.')


class PPGUpdate(_PPGUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        args_schema.tags._registered = False
        args_schema.zone._registered = False
        args_schema.colocation_status._registered = False
        args_schema.location._registered = False
        args_schema.proximity_placement_group_name._id_part = None

        return args_schema
