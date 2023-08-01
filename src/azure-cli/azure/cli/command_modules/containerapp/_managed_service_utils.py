# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.azclierror import ValidationError


class ManagedRedisUtils:

    @staticmethod
    def build_redis_resource_id(subscription_id, resource_group_name, service_name, arg_dict):
        url_fmt = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Cache/redis/{}/databases/{}"
        resource_id = url_fmt.format(
            subscription_id,
            resource_group_name,
            service_name,
            arg_dict["database"] if "database" in arg_dict else "0")
        return resource_id

    @staticmethod
    def build_redis_params(resource_id, capp_name, key_vault_id):
        parameters = {
            'target_service': {
                "type": "AzureResource",
                "id": resource_id
            },
            "auth_info": {
                "auth_type": "secret"
            },
            'secret_store': {
                'key_vault_id': key_vault_id,
            },
            'scope': capp_name,
        }
        return parameters

    @staticmethod
    def build_redis_service_connector_def(subscription_id, resource_group_name, service_name, arg_dict, name,
                                          binding_name):
        resource_id = ManagedRedisUtils.build_redis_resource_id(subscription_id, resource_group_name, service_name,
                                                                arg_dict)
        parameters = ManagedRedisUtils.build_redis_params(resource_id, name, key_vault_id=None)
        return {"linker_name": binding_name, "parameters": parameters, "resource_id": resource_id}


class ManagedCosmosDBUtils:

    @staticmethod
    def build_cosmos_resource_id(subscription_id, resource_group_name, service_name, arg_dict):
        url_fmt = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DocumentDB/" \
                  "databaseAccounts/{}/mongodbDatabases/{}"
        resource_id = url_fmt.format(
            subscription_id,
            resource_group_name,
            service_name,
            arg_dict["database"])
        return resource_id

    @staticmethod
    def build_cosmos_params(resource_id, capp_name, key_vault_id):
        parameters = {
            'target_service': {
                "type": "AzureResource",
                "id": resource_id
            },
            'auth_info': {
                'auth_type': "systemAssignedIdentity"
            },
            'secret_store': {
                'key_vault_id': key_vault_id,
            },
            'scope': capp_name,
        }
        return parameters

    @staticmethod
    def build_cosmosdb_service_connector_def(subscription_id, resource_group_name, service_name, arg_dict, name,
                                             binding_name):
        if "database" not in arg_dict:
            raise ValidationError("Managed Cosmos DB needs the database argument.")
        resource_id = ManagedCosmosDBUtils.build_cosmos_resource_id(subscription_id, resource_group_name, service_name,
                                                                    arg_dict)
        parameters = ManagedCosmosDBUtils.build_cosmos_params(resource_id, name, key_vault_id=None)
        return {"linker_name": binding_name, "parameters": parameters, "resource_id": resource_id}


class ManagedPostgreSQLUtils:

    @staticmethod
    def build_postgres_resource_id(subscription_id, resource_group_name, service_name, arg_dict):
        url_fmt = "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.DBforPostgreSQL/flexibleServers/" \
                  "{}/databases/{}"
        resource_id = url_fmt.format(
            subscription_id,
            resource_group_name,
            service_name,
            arg_dict["database"])
        return resource_id

    @staticmethod
    def build_postgres_params(resource_id, capp_name, username, password, key_vault_id):
        parameters = {
            'target_service': {
                "type": "AzureResource",
                "id": resource_id
            },
            'auth_info': {
                'authType': "secret",
                'secret_info': {
                    'secret_type': "rawValue",
                    'value': password,
                },
                'name': username
            },
            'secret_store': {
                'key_vault_id': key_vault_id,
            },
            'scope': capp_name,
        }
        return parameters

    @staticmethod
    def build_postgresql_service_connector_def(subscription_id, resource_group_name, service_name, arg_dict, name,
                                               binding_name):
        if not all(key in arg_dict for key in ["database", "username", "password"]):
            raise ValidationError(
                "Managed PostgreSQL Flexible Server needs the database, username, and password arguments.")
        resource_id = ManagedPostgreSQLUtils.build_postgres_resource_id(subscription_id, resource_group_name,
                                                                        service_name, arg_dict)
        parameters = ManagedPostgreSQLUtils.build_postgres_params(resource_id, name, arg_dict["username"],
                                                                  arg_dict["password"], key_vault_id=None)
        return {"linker_name": binding_name, "parameters": parameters, "resource_id": resource_id}
