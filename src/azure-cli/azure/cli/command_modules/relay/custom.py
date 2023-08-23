# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from .aaz.latest.relay.hyco import Update as _HycoUpdate
from .aaz.latest.relay.hyco.authorization_rule import Create as _HycoAuthoCreate, Update as _HycoAuthoUpdate
from .aaz.latest.relay.namespace.authorization_rule import Create as _NamespaceAuthoCreate
from .aaz.latest.relay.wcfrelay import Update as _WcfrelayUpdate
from .aaz.latest.relay.wcfrelay.authorization_rule import Create as _WcfrelayAuthoCreate, Update as _WcfrelayAuthoUpdate


# pylint: disable=line-too-long
# pylint: disable=too-many-lines
# pylint: disable=inconsistent-return-statements
# pylint: disable=unused-variable
# pylint: disable=protected-access


class NamespaceAuthoCreate(_NamespaceAuthoCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.rights._required = False
        return args_schema


class WcfrelayAuthoCreate(_WcfrelayAuthoCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.rights._required = False
        return args_schema


class WcfrelayAuthoUpdate(_WcfrelayAuthoUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.rights._required = True
        return args_schema


class HycoAuthoCreate(_HycoAuthoCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.rights._required = False
        return args_schema


class HycoAuthoUpdate(_HycoAuthoUpdate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.rights._required = True
        return args_schema


class WcfrelayUpdate(_WcfrelayUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.status = AAZStrArg(
            options=["--status"],
            help="Enumerates the possible values for the status of a messaging entity.",
            enum={"Active": "Active", "Disabled": "Disabled", "ReceiveDisabled": "ReceiveDisabled", "SendDisabled": "SendDisabled"},
            nullable=True
        )
        return args_schema


class HycoUpdate(_HycoUpdate):
    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZStrArg
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.status = AAZStrArg(
            options=["--status"],
            help="Enumerates the possible values for the status of a messaging entity.",
            enum={"Active": "Active", "Disabled": "Disabled", "ReceiveDisabled": "ReceiveDisabled", "SendDisabled": "SendDisabled"},
            nullable=True
        )
        return args_schema
