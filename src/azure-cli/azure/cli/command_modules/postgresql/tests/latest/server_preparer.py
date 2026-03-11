# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import random
from azure.cli.testsdk.base import execute
from azure.cli.testsdk.preparers import (
    AbstractPreparer,
    SingleValueReplacer)
from .constants import SERVER_NAME_PREFIX, SERVER_NAME_MAX_LENGTH, DEFAULT_LOCATION


class ServerPreparer(AbstractPreparer, SingleValueReplacer):

    def __init__(self, location=DEFAULT_LOCATION, name_prefix=SERVER_NAME_PREFIX,
                 resource_group_parameter_name='resource_group'):
        super().__init__(name_prefix, SERVER_NAME_MAX_LENGTH)
        from azure.cli.core.mock import DummyCli
        self.cli_ctx = DummyCli()
        self.location = location
        self.resource_group_parameter_name = resource_group_parameter_name

    # Create server with at least 4 vCores and running PostgreSQL major version of 13 or later
    def create_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        version = '17'
        storage_size = 128
        sku_name = self.get_random_sku_name()
        tier = 'GeneralPurpose'
        template = 'postgres flexible-server create -g {} -n {} --sku-name {} --tier {} --storage-size {} --version {} -l {} --public-access none --yes'
        execute(self.cli_ctx, template.format(group, name, sku_name, tier, storage_size, version, self.location))
        return {'server': name }

    def remove_resource(self, name, **kwargs):
        group = self._get_resource_group(**kwargs)
        execute(self.cli_ctx, 'az postgres flexible-server delete -g {} -n {} --yes'.format(group, name))

    def _get_resource_group(self, **kwargs):
        return kwargs.get(self.resource_group_parameter_name)
    
    def get_random_sku_name(self):
        """Returns a random SKU name from available options."""
        sku_options = [
            'Standard_D4ds_v4',
            'Standard_D4ds_v5', 
            'Standard_D4ads_v5',
            'Standard_D2ds_v5',
            'Standard_D2ds_v4'
        ]
        return random.choice(sku_options)
    