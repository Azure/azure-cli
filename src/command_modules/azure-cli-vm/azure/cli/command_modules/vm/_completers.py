# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def get_urn_aliases_completion_list(prefix, **kwargs):  # pylint: disable=unused-argument
    images = load_images_from_aliases_doc()
    return [i['urnAlias'] for i in images]


def get_vm_size_completion_list(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
    try:
        location = parsed_args.location
    except AttributeError:
        location = get_one_of_subscription_locations()
    result = get_vm_sizes(location)
    return [r.name for r in result]


def get_vm_run_command_completion_list(prefix, action, parsed_args, **kwargs):  # pylint: disable=unused-argument
    from ._client_factory import _compute_client_factory
    try:
        location = parsed_args.location
    except AttributeError:
        location = get_one_of_subscription_locations()
    result = _compute_client_factory().virtual_machine_run_commands.list(location)
    return [r.id for r in result]
