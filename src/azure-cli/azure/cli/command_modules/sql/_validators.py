# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import CLIError

# Important note: if cmd validator exists, then individual param validators will not be
# executed. See C:\git\azure-cli\env\lib\site-packages\knack\invocation.py `def _validation`


def create_args_for_complex_type(arg_ctx, dest, model_type, arguments):
    '''
    Creates args that will be combined into an object by an arg validator.
    '''

    from knack.arguments import ignore_type
    from knack.introspection import option_descriptions

    def get_complex_argument_processor(expanded_arguments, assigned_arg, model_type):
        '''
        Return a validator which will aggregate multiple arguments to one complex argument.
        '''

        def _expansion_validator_impl(namespace):
            '''
            The validator create a argument of a given type from a specific set of arguments from CLI
            command.
            :param namespace: The argparse namespace represents the CLI arguments.
            :return: The argument of specific type.
            '''
            ns = vars(namespace)
            kwargs = dict((k, ns[k]) for k in ns if k in set(expanded_arguments))
            setattr(namespace, assigned_arg, model_type(**kwargs))

        return _expansion_validator_impl

    # Fetch the documentation for model parameters first. for models, which are the classes
    # derive from msrest.serialization.Model and used in the SDK API to carry parameters, the
    # document of their properties are attached to the classes instead of constructors.
    parameter_docs = option_descriptions(model_type)

    for name in arguments:
        # Get the validation map from the model type in order to determine
        # whether the argument should be required
        validation = model_type._validation.get(name, None)  # pylint: disable=protected-access
        required = validation.get('required', False) if validation else False

        # Generate the command line argument name from the property name
        options_list = ['--' + name.replace('_', '-')]

        # Get the help text from the model type
        help_text = parameter_docs.get(name, None)

        # Create the additional command line argument
        arg_ctx.extra(
            name,
            required=required,
            options_list=options_list,
            help=help_text)

    # Rename the original command line argument and ignore it (i.e. make invisible)
    # so that it does not show up on command line and does not conflict with any other
    # arguments.
    dest_option = ['--__{}'.format(dest.upper())]

    arg_ctx.argument(dest,
                     arg_type=ignore_type,
                     options_list=dest_option,
                     # The argument is hidden from the command line, but its value
                     # will be populated by this validator.
                     validator=get_complex_argument_processor(arguments, dest, model_type))


###############################################
#                sql server vnet-rule         #
###############################################


# Validates if a subnet id or name have been given by the user. If subnet id is given, vnet-name should not be provided.
def validate_subnet(cmd, namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id
    from azure.cli.core.commands.client_factory import get_subscription_id

    # Different custom function arg names, instance pool has subnet_id
    is_instance_pool = False
    if hasattr(namespace, "subnet_id"):
        is_instance_pool = True
        subnet = namespace.subnet_id
    else:
        subnet = namespace.virtual_network_subnet_id

    subnet_is_id = is_valid_resource_id(subnet)
    vnet = namespace.vnet_name

    if (subnet_is_id and not vnet) or (not subnet and not vnet):
        pass
    elif subnet and not subnet_is_id and vnet:
        virtual_network_subnet_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet,
            child_type_1='subnets',
            child_name_1=subnet)
        if is_instance_pool:
            namespace.subnet_id = virtual_network_subnet_id
        else:
            namespace.virtual_network_subnet_id = virtual_network_subnet_id
    else:
        raise CLIError('incorrect usage: [--subnet ID | --subnet NAME --vnet-name NAME]')
    delattr(namespace, 'vnet_name')


###############################################
#                   sql db                    #
###############################################

def validate_backup_storage_redundancy(namespace):
    # Validate if entered backup storage redundancy value is within allowed values
    if (not namespace.requested_backup_storage_redundancy or
            (namespace.requested_backup_storage_redundancy and
             namespace.requested_backup_storage_redundancy in ['Local', 'Zone', 'Geo', 'GeoZone'])):
        pass
    else:
        raise CLIError('incorrect usage: --backup-storage-redundancy must be either Local, Zone, Geo or GeoZone')


###############################################
#                sql managed instance         #
###############################################


def validate_managed_instance_storage_size(namespace):
    # Validate if entered storage size value is an increment of 32 if provided
    if (not namespace.storage_size_in_gb) or (namespace.storage_size_in_gb and namespace.storage_size_in_gb % 32 == 0):
        pass
    else:
        raise CLIError('incorrect usage: --storage must be specified in increments of 32 GB')
