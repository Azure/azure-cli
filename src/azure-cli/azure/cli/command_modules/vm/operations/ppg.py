# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from ..aaz.latest.ppg import Show as _PPGShow

logger = get_logger(__name__)


class PPGShow(_PPGShow):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)

        from azure.cli.core.aaz import AAZArgEnum
        args_schema.include_colocation_status._blank = "True"
        args_schema.include_colocation_status.enum = AAZArgEnum({"True": "True", "False": "False"})

        return args_schema
