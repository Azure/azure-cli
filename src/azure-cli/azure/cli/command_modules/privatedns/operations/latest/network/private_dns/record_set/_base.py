# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods, no-self-use, line-too-long, protected-access, unused-argument
from azure.cli.command_modules.privatedns.aaz.latest.network.private_dns.record_set._create import Create as _RecordSetCreate
from azure.cli.command_modules.privatedns.aaz.latest.network.private_dns.record_set._delete import Delete as _RecordSetDelete
from azure.cli.command_modules.privatedns.aaz.latest.network.private_dns.record_set._list_by_type import ListByType as _RecordSetList
from azure.cli.command_modules.privatedns.aaz.latest.network.private_dns.record_set._show import Show as _RecordSetShow
from azure.cli.command_modules.privatedns.aaz.latest.network.private_dns.record_set._update import Update as _RecordSetUpdate


# region RecordSetCreate
class RecordSetCreate(_RecordSetCreate):
    AZ_NAME = None

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.record_type._required = False
        args_schema.record_type._registered = False
        args_schema.if_none_match._registered = False
        args_schema.a_records._registered = False
        args_schema.aaaa_records._registered = False
        args_schema.cname_record._registered = False
        args_schema.mx_records._registered = False
        args_schema.ptr_records._registered = False
        args_schema.soa_record._registered = False
        args_schema.srv_records._registered = False
        args_schema.txt_records._registered = False

        return args_schema
# endregion RecordSetCreate


# region RecordSetDelete
class RecordSetDelete(_RecordSetDelete):
    AZ_NAME = None

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.record_type._required = False
        args_schema.record_type._registered = False

        return args_schema
# endregion RecordSetDelete


# region RecordSetList
class RecordSetList(_RecordSetList):
    AZ_NAME = None

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.record_type._required = False
        args_schema.record_type._registered = False

        return args_schema
# endregion RecordSetList


# region RecordSetShow
class RecordSetShow(_RecordSetShow):
    AZ_NAME = None

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.record_type._required = False
        args_schema.record_type._registered = False

        return args_schema
# endregion RecordSetShow


# region RecordSetUpdate
class RecordSetUpdate(_RecordSetUpdate):
    AZ_NAME = None

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.record_type._required = False
        args_schema.record_type._registered = False
        args_schema.a_records._registered = False
        args_schema.aaaa_records._registered = False
        args_schema.cname_record._registered = False
        args_schema.mx_records._registered = False
        args_schema.ptr_records._registered = False
        args_schema.soa_record._registered = False
        args_schema.srv_records._registered = False
        args_schema.txt_records._registered = False

        return args_schema
# endregion RecordSetUpdate
