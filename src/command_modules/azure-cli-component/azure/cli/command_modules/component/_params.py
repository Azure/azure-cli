# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


# pylint: disable=line-too-long
def load_arguments(self, _):

    with self.argument_context('component') as c:
        c.argument('component_name', options_list=['--name', '-n'], help='Name of component')
        c.argument('link', options_list=['--link', '-l'], help='If a url or path to an html file, parse for links to archives. If local path or file:// url that\'s a directory, then look for archives in the directory listing.')
        c.argument('private', help='Include packages from a private server.', action='store_true')
        c.argument('pre', help='Include pre-release versions', action='store_true')
        c.argument('additional_components', options_list=['--add'], nargs='+', help='The names of additional components to install (space separated)')
        c.argument('allow_third_party', options_list=['--allow-third-party'], action='store_true', help='Allow installation of 3rd party command modules. This option is assumed with --private.')
