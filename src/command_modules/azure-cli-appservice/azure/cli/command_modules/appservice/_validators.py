# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError

from ._client_factory import web_client_factory

FUNCTION_APP_TYPES = ['functionapp', 'functionapp,linux']
WEB_APP_TYPES = ['app', 'app,linux']


def validate_existing_function_app(namespace):
    validate_existing_app(namespace, FUNCTION_APP_TYPES)


def validate_existing_web_app(namespace):
    validate_existing_app(namespace, WEB_APP_TYPES)


def validate_existing_app(namespace, app_type):
    client = web_client_factory()
    instance = client.web_apps.get(namespace.resource_group_name, namespace.name)
    if instance.kind not in app_type:  # pylint: disable=no-member
        raise CLIError('Usage Error: {} is not a correct app type'.format(namespace.name))
    setattr(namespace, 'app_instance', instance)
