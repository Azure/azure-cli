# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.commands.client_factory import get_subscription_id
from azure.cli.core.util import CLIError

# Important note: if cmd validator exists, then individual param validators will not be
# executed. See C:\git\azure-cli\env\lib\site-packages\knack\invocation.py `def _validation`


def expand(arg_ctx, dest, model_type, arguments):
    # TODO:
    # two privates symbols are imported here. they should be made public or this utility class
    # should be moved into azure.cli.core
    from knack.arguments import CLIArgumentType, ignore_type
    from knack.introspection import option_descriptions

    # fetch the documentation for model parameters first. for models, which are the classes
    # derive from msrest.serialization.Model and used in the SDK API to carry parameters, the
    # document of their properties are attached to the classes instead of constructors.
    parameter_docs = option_descriptions(model_type)

    def get_complex_argument_processor(expanded_arguments, assigned_arg, model_type):
        """
        Return a validator which will aggregate multiple arguments to one complex argument.
        """

        def _expansion_validator_impl(namespace):
            """
            The validator create a argument of a given type from a specific set of arguments from CLI
            command.
            :param namespace: The argparse namespace represents the CLI arguments.
            :return: The argument of specific type.
            """
            ns = vars(namespace)
            kwargs = dict((k, ns[k]) for k in ns if k in set(expanded_arguments))
            setattr(namespace, assigned_arg, model_type(**kwargs))

        return _expansion_validator_impl

    for name in arguments:
        validation = model_type._validation.get(name, None)
        required = validation.get('required', False) if validation else False
        options_list = ['--' + name.replace('_', '-')]
        help = parameter_docs.get(name, None)

        arg_ctx.extra(
            name,
            required=required,
            options_list=options_list,
            help=help)

    dest_option = ['--__{}'.format(dest.upper())]

    arg_ctx.argument(dest,
                  arg_type=ignore_type,
                  options_list=dest_option,
                  validator=get_complex_argument_processor(arguments, dest, model_type))


###############################################
#                sql db                       #
###############################################


def validate_elastic_pool_id(cmd, namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id

    # If elastic_pool_id is specified but it is not a valid resource id,
    # then assume that user specified elastic pool name which we need to
    # convert to elastic pool id.
    if namespace.elastic_pool_id and not is_valid_resource_id(namespace.elastic_pool_id):
        namespace.elastic_pool_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Sql',
            type='servers',
            name=namespace.server_name,
            child_type_1='elasticPools',
            child_name_1=namespace.elastic_pool_id)


###############################################
#                sql server vnet-rule         #
###############################################


# Validates if a subnet id or name have been given by the user. If subnet id is given, vnet-name should not be provided.
def validate_subnet(cmd, namespace):
    from msrestazure.tools import resource_id, is_valid_resource_id

    subnet = namespace.virtual_network_subnet_id
    subnet_is_id = is_valid_resource_id(subnet)
    vnet = namespace.vnet_name

    if (subnet_is_id and not vnet) or (not subnet and not vnet):
        pass
    elif subnet and not subnet_is_id and vnet:
        namespace.virtual_network_subnet_id = resource_id(
            subscription=get_subscription_id(cmd.cli_ctx),
            resource_group=namespace.resource_group_name,
            namespace='Microsoft.Network',
            type='virtualNetworks',
            name=vnet,
            child_type_1='subnets',
            child_name_1=subnet)
    else:
        raise CLIError('incorrect usage: [--subnet ID | --subnet NAME --vnet-name NAME]')
    delattr(namespace, 'vnet_name')
