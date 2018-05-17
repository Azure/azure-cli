# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.prompting import prompt_pass, NoTTYException
from knack.util import CLIError

from azure.cli.core.commands.validators import (
    get_default_location_from_resource_group, validate_tags)


def get_combined_validator(validators):
    def _final_validator_impl(cmd, namespace):
        # do additional creation validation
        verb = cmd.name.rsplit(' ', 1)[1]
        if verb == 'create':
            password_validator(namespace)
            get_default_location_from_resource_group(cmd, namespace)

        validate_tags(namespace)

        for validator in validators:
            validator(namespace)

    return _final_validator_impl


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
