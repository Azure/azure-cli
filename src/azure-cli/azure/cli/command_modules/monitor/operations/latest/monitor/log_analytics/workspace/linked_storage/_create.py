# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=protected-access

from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace.linked_storage._create \
    import Create as _WorkspaceLinkedStorageAccountCreate


class WorkspaceLinkedStorageAccountCreate(_WorkspaceLinkedStorageAccountCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat
        cls._args_schema = super()._build_arguments_schema(*args, **kwargs)

        storage_accounts = cls._args_schema.storage_accounts
        storage_accounts._element = AAZResourceIdArg(fmt=AAZResourceIdArgFormat(
            template='/subscriptions/{subscription}/resourceGroups/{resource_group}/'
                     'providers/Microsoft.Storage/storageAccounts/{}'))
        return cls._args_schema
