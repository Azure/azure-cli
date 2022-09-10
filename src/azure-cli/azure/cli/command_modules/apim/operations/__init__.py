# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.command_modules.apim.operations.api import ApiOperations
from azure.cli.command_modules.apim.operations.api_policy import ApiPolicyOperations
from azure.cli.command_modules.apim.operations.api_operation import ApiOperationOperations
from azure.cli.command_modules.apim.operations.api_release import ApiReleaseOperations
from azure.cli.command_modules.apim.operations.api_revision import ApiRevisionOperations
from azure.cli.command_modules.apim.operations.api_schema import ApiSchemaOperations
from azure.cli.command_modules.apim.operations.api_version_set import ApiVersionSetOperations
from azure.cli.command_modules.apim.operations.deleted_service import DeletedServiceOperations
from azure.cli.command_modules.apim.operations.named_value import NamedValueOperations
from azure.cli.command_modules.apim.operations.policy import PolicyOperations
from azure.cli.command_modules.apim.operations.product import ProductOperations
from azure.cli.command_modules.apim.operations.product_api import ProductApiOperations
from azure.cli.command_modules.apim.operations.subscription import SubscriptionOperations


class ApimSubgroupsLoader():
    def __init__(self, commands_loader):
        self.commands_loader = commands_loader
        self.subgroup_command_loaders = [
            ApiOperations(self),
            ApiOperationOperations(self),
            ApiPolicyOperations(self),
            ApiReleaseOperations(self),
            ApiRevisionOperations(self),
            ApiSchemaOperations(self),
            ApiVersionSetOperations(self),
            DeletedServiceOperations(self),
            NamedValueOperations(self),
            PolicyOperations(self),
            ProductOperations(self),
            ProductApiOperations(self),
            SubscriptionOperations(self)
        ]

    def load_arguments(self, _):
        for command_loader in self.subgroup_command_loaders:
            command_loader.load_arguments(_)

    def load_command_table(self, _):
        for command_loader in self.subgroup_command_loaders:
            command_loader.load_command_table(_)
