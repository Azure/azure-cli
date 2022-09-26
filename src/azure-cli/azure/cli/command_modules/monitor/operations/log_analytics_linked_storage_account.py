# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.monitor.aaz.latest.monitor.log_analytics.workspace.linked_storage import \
    Create as _WorkspaceLinkedStorageAccountCreate, Update as _WorkspaceLinkedStorageAccountUpdate


class WorkspaceLinkedStorageAccountCreate(_WorkspaceLinkedStorageAccountCreate):

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        from azure.cli.core.aaz import AAZResourceIdArg, AAZResourceIdArgFormat
        cls._args_schema = super()._build_arguments_schema(*args, **kwargs)

        storage_accounts = cls._args_schema.storage_accounts
        storage_accounts._element = AAZResourceIdArg(fmt=AAZResourceIdArgFormat(  # pylint: disable=protected-access
            template='/subscriptions/{subscription}/resourceGroups/{resource_group}/'
                     'providers/Microsoft.Storage/storageAccounts/{}'))
        return cls._args_schema


def add_log_analytics_workspace_linked_storage_accounts(cmd, resource_group_name, workspace_name,
                                                        data_source_type, storage_account_ids):
    class Add(_WorkspaceLinkedStorageAccountUpdate):

        def pre_instance_update(self, instance):
            instance.properties.storage_account_ids.extend(storage_account_ids)

    return Add(cli_ctx=cmd.cli_ctx)(command_args={
        "data_source_type": data_source_type,
        "resource_group": resource_group_name,
        "workspace_name": workspace_name
    })


def remove_log_analytics_workspace_linked_storage_accounts(cmd, resource_group_name, workspace_name,
                                                           data_source_type, storage_account_ids):
    class Remove(_WorkspaceLinkedStorageAccountUpdate):

        def pre_instance_update(self, instance):
            storage_account_ids_set = set(str.lower(storage_account_id) for storage_account_id in storage_account_ids)
            new_storage_account_ids = []
            for existed_storage_account_id in instance.properties.storage_account_ids:
                if str(existed_storage_account_id).lower() in storage_account_ids_set:
                    continue
                new_storage_account_ids.append(existed_storage_account_id)
            instance.properties.storage_account_ids = new_storage_account_ids

    return Remove(cli_ctx=cmd.cli_ctx)(command_args={
        "data_source_type": data_source_type,
        "resource_group": resource_group_name,
        "workspace_name": workspace_name
    })
