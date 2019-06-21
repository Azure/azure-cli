# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long

from knack.arguments import CLIArgumentType


def load_arguments(self, _):

    from azure.cli.core.commands.parameters import tags_type
    from azure.cli.core.commands.validators import get_default_location_from_resource_group

    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis_name', apimgmt apis_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis_name', apimgmt apis_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis_name', apimgmt apis_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis releases') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis releases_name', apimgmt apis releases_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis releases') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis releases') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis releases') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis releases') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis releases') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis releases') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis releases_name', apimgmt apis releases_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis releases') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis releases') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis operations') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis operations_name', apimgmt apis operations_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis operations') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis operations') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis operations') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis operations') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis operations') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis operations') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis operations_name', apimgmt apis operations_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis operations') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis operations') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis operations policies') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis operations policies_name', apimgmt apis operations policies_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis operations policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis operations policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis operations policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis operations policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis operations policies') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis operations policies_name', apimgmt apis operations policies_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis operations policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis operations policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt tags') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt tags_name', apimgmt tags_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt tags') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt tags') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt tags') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt tags') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt tags') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt tags apis products operations') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt tags apis products operations_name', apimgmt tags apis products operations_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt tags apis products operations') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt tags apis products operations') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis_name', apimgmt apis_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis policies') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis policies_name', apimgmt apis policies_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis policies') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis policies_name', apimgmt apis policies_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis schemas') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis schemas_name', apimgmt apis schemas_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis schemas') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis schemas') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis schemas') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis schemas') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis schemas') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis schemas_name', apimgmt apis schemas_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis schemas') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis schemas') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis diagnostics') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis diagnostics_name', apimgmt apis diagnostics_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis diagnostics') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis diagnostics') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis diagnostics') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis diagnostics') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis diagnostics') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis diagnostics') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis diagnostics_name', apimgmt apis diagnostics_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis diagnostics') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis diagnostics') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis issues') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis issues_name', apimgmt apis issues_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis issues') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis issues') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis issues') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis issues') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis issues') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis issues') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis issues_name', apimgmt apis issues_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis issues') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis issues') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis issues comments') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis issues comments_name', apimgmt apis issues comments_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis issues comments') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis issues comments') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis issues comments') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis issues comments') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis issues comments') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis issues comments_name', apimgmt apis issues comments_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis issues comments') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis issues comments') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis issues attachments') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis issues attachments_name', apimgmt apis issues attachments_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis issues attachments') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis issues attachments') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis issues attachments') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis issues attachments') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis issues attachments') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis issues attachments_name', apimgmt apis issues attachments_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis issues attachments') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis issues attachments') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis tagdescriptions') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis tagdescriptions_name', apimgmt apis tagdescriptions_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis tagdescriptions') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis tagdescriptions') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis tagdescriptions') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis tagdescriptions') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis tagdescriptions') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis tagdescriptions_name', apimgmt apis tagdescriptions_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis tagdescriptions') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apis tagdescriptions') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis_name', apimgmt apis_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apiversionsets') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apiversionsets_name', apimgmt apiversionsets_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apiversionsets') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apiversionsets') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apiversionsets') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apiversionsets') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apiversionsets') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apiversionsets') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apiversionsets_name', apimgmt apiversionsets_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apiversionsets') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt apiversionsets') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt authorizationservers') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt authorizationservers_name', apimgmt authorizationservers_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt authorizationservers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt authorizationservers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt authorizationservers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt authorizationservers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt authorizationservers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt authorizationservers') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt authorizationservers_name', apimgmt authorizationservers_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt authorizationservers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt authorizationservers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt backends') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt backends_name', apimgmt backends_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt backends') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt backends') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt backends') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt backends') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt backends') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt backends') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt backends_name', apimgmt backends_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt backends') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt backends') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt caches') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt caches_name', apimgmt caches_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt caches') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt caches') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt caches') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt caches') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt caches') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt caches') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt caches_name', apimgmt caches_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt caches') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt caches') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt certificates') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt certificates_name', apimgmt certificates_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt certificates') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt certificates') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt certificates') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt certificates') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt certificates') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt certificates_name', apimgmt certificates_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt certificates') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt certificates') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('_name', _name_type, options_list=['--name', '-n'])

    with self.argument_context('') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt_name', apimgmt_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt_name', apimgmt_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt_name', apimgmt_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt diagnostics') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt diagnostics_name', apimgmt diagnostics_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt diagnostics') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt diagnostics') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt diagnostics') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt diagnostics') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt diagnostics') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt diagnostics') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt diagnostics_name', apimgmt diagnostics_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt diagnostics') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt diagnostics') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt templates') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt templates_name', apimgmt templates_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt templates') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt templates') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt templates') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt templates') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt templates') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt templates') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt templates_name', apimgmt templates_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt templates') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt templates') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt groups') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt groups_name', apimgmt groups_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt groups') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt groups') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt groups') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt groups') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt groups') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt groups') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt groups_name', apimgmt groups_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt groups') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt groups') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt groups users') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt groups users_name', apimgmt groups users_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt groups users') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt groups users') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt groups users') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt groups') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt groups_name', apimgmt groups_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt groups') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt identityproviders') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt identityproviders_name', apimgmt identityproviders_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt identityproviders') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt identityproviders') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt identityproviders') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt identityproviders') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt identityproviders') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt identityproviders') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt identityproviders_name', apimgmt identityproviders_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt identityproviders') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt identityproviders') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt issues') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt issues_name', apimgmt issues_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt issues') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt issues') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt loggers') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt loggers_name', apimgmt loggers_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt loggers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt loggers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt loggers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt loggers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt loggers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt loggers') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt loggers_name', apimgmt loggers_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt loggers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt loggers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt locations') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt locations_name', apimgmt locations_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt locations') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt notifications') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt notifications_name', apimgmt notifications_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt notifications') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt notifications') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt notifications') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt notifications') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt notifications_name', apimgmt notifications_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt notifications') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt notifications') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt notifications recipientusers') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt notifications recipientusers_name', apimgmt notifications recipientusers_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt notifications recipientusers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt notifications recipientusers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt notifications recipientusers') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt notifications') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt notifications_name', apimgmt notifications_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt notifications') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt notifications recipientemails') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt notifications recipientemails_name', apimgmt notifications recipientemails_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt notifications recipientemails') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt notifications recipientemails') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt notifications recipientemails') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt notifications') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt notifications_name', apimgmt notifications_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt notifications') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt openidconnectproviders') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt openidconnectproviders_name', apimgmt openidconnectproviders_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt openidconnectproviders') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt openidconnectproviders') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt openidconnectproviders') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt openidconnectproviders') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt openidconnectproviders') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt openidconnectproviders') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt openidconnectproviders_name', apimgmt openidconnectproviders_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt openidconnectproviders') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt openidconnectproviders') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt policies') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt policies_name', apimgmt policies_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt policies') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt policies_name', apimgmt policies_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt_name', apimgmt_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt_name', apimgmt_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt_name', apimgmt_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt_name', apimgmt_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt_name', apimgmt_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt_name', apimgmt_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt_name', apimgmt_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt products') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt products_name', apimgmt products_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt products') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt products') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt products') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt products') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt products') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt products') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt products_name', apimgmt products_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt products') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt products') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt products apis') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt products apis_name', apimgmt products apis_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt products apis') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt products apis') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt products apis') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt products') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt products_name', apimgmt products_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt products') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt products groups') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt products groups_name', apimgmt products groups_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt products groups') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt products groups') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt products groups') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt products') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt products_name', apimgmt products_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt products') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt products') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt products_name', apimgmt products_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt products') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt products policies') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt products policies_name', apimgmt products policies_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt products policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt products policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt products policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt products policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt products policies') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt products policies_name', apimgmt products policies_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt products policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt products policies') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt properties') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt properties_name', apimgmt properties_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt properties') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt properties') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt properties') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt properties') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt properties') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt properties') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt properties_name', apimgmt properties_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt properties') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt properties') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt quotas') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt quotas_name', apimgmt quotas_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt quotas') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt quotas periods') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt quotas periods_name', apimgmt quotas periods_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt quotas periods') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt_name', apimgmt_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt_name', apimgmt_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt subscriptions') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt subscriptions_name', apimgmt subscriptions_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt subscriptions') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt subscriptions') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt subscriptions') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt subscriptions') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt subscriptions') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt subscriptions') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt subscriptions_name', apimgmt subscriptions_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt subscriptions') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt subscriptions') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt_name', apimgmt_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt tenant') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt tenant_name', apimgmt tenant_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt tenant') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt tenant') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt tenant_name', apimgmt tenant_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt tenant') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt tenant') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt tenant_name', apimgmt tenant_name_type, options_list=['--name', '-n'])
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt users') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt users_name', apimgmt users_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt users') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt users') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt users') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt users') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt users') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt users') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt users_name', apimgmt users_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt users') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)

    with self.argument_context('apimgmt users') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt users') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt users_name', apimgmt users_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt users') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt users') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt users_name', apimgmt users_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt users') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt users') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt users_name', apimgmt users_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt users') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimgmt apis') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimgmt apis_name', apimgmt apis_name_type, options_list=['--name', '-n'])

    with self.argument_context('apimgmt apis') as c:
        c.argument('apimgmt_name', apimgmt_name_type, id_part=None)
    apimanagement_name_type = CLIArgumentType(options_list='--apimanagement-name-name', help='Name of the Apimanagement.', id_part='name')

    with self.argument_context('apimanagement') as c:
        c.argument('tags', tags_type)
        c.argument('location', validator=get_default_location_from_resource_group)
        c.argument('apimanagement_name', apimanagement_name_type, options_list=['--name', '-n'])