# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core._util import CLIError
from azure.cli.core.commands.validators import get_default_location_from_resource_group

def _validate_plan_arg(namespace):
    from ._client_factory import web_client_factory
    namespace.create_plan = False
    if namespace.plan:
        from azure.cli.core.commands.arm import is_valid_resource_id
        if not is_valid_resource_id(namespace.plan):
            from msrestazure.azure_exceptions import CloudError
            client = web_client_factory()
            try:
                client.app_service_plans.get(namespace.resource_group_name, namespace.plan)
            except CloudError:
                namespace.create_plan = True
    else:
        client = web_client_factory()
        result = client.app_service_plans.list_by_resource_group(namespace.resource_group_name)
        existing_plan = next((x for x in result if _match_plan_location(x, namespace.location) and
                              namespace.is_linux == (x.kind == 'linux')), None)
        if existing_plan:
            namespace.plan = existing_plan.id
        else:
            namespace.create_plan = True
            namespace.plan = namespace.name + '_plan'

    if not namespace.create_plan and (namespace.sku or namespace.number_of_workers):
        raise CLIError('Usage error: argument values for --sku or --number-of-workers will '
                       'be ignored, as the new web will be created using an existing '
                       'plan {}. Please use --plan to specify a new plan'.format(namespace.plan))



def _match_plan_location(plan, location):
    # the problem with appservice is it uses display name, rather canonical name
    # so we have to hack it
    return plan.location.replace(' ', '').lower() == location.lower()


def process_webapp_create_namespace(namespace):
    get_default_location_from_resource_group(namespace)
    _validate_plan_arg(namespace)
