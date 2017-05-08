# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.validators import \
    (get_default_location_from_resource_group, validate_tags)
from azure.cli.core.prompting import prompt_pass, NoTTYException
from azure.cli.core.util import CLIError


def get_combined_validator(validators):
    def _final_valiator_impl(namespace):
        # do additional creation validation
        if namespace.subcommand == 'create':
            storage_validator(namespace)
            password_validator(namespace)
            get_default_location_from_resource_group(namespace)

        validate_tags(namespace)

        for validator in validators:
            validator(namespace)

        if namespace.sku.tier or namespace.sku.capacity:
            namespace.sku.name = 'SkuName'
        else:
            namespace.parameters.sku = None

    return _final_valiator_impl


def configuration_value_validator(ns):
    val = ns.value
    if val is None or not val.strip():
        ns.value = None
        ns.source = 'system-default'


def password_validator(ns):
    if not ns.administrator_login_password:
        try:
            ns.administrator_login_password = prompt_pass(msg='Admin Password: ')
        except NoTTYException:
            raise CLIError('Please specify password in non-interactive mode.')


def storage_validator(ns):
    if ns.storage_mb:
        if ns.storage_mb > 1023 * 1024:
            raise ValueError('The size of storage cannot exceed 1023GB.')
