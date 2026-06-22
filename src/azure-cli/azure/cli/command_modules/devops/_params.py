# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


def load_arguments(self, _):
    with self.argument_context('artifacts universal') as c:
        c.argument('name', options_list=['--name', '-n'],
                   help='Name of the package, e.g. \'foo-package\'.')
        c.argument('version', options_list=['--version', '-v'],
                   help='Version of the package, e.g. \'1.0.0\'.')
        c.argument('feed', options_list=['--feed'],
                   help='Name or ID of the feed.')
        c.argument('scope', options_list=['--scope'],
                   help='Scope of the feed: \'project\' if the feed was created in a project, '
                        'and \'organization\' otherwise.',
                   choices=['project', 'organization'])
        c.argument('organization', options_list=['--organization', '--org'],
                   help='Azure DevOps organization URL. You can configure the default organization '
                        'using az devops configure -d organization=ORG_URL. '
                        'Required if not configured as default or picked up via git config.')
        c.argument('project', options_list=['--project', '-p'],
                   help='Name or ID of the project. You can configure the default project using '
                        'az devops configure -d project=NAME_OR_ID. '
                        'Required if not configured as default or picked up via git config.')
        c.argument('detect', options_list=['--detect'],
                   help='Automatically detect organization.',
                   choices=['true', 'false'])

    with self.argument_context('artifacts universal download') as c:
        c.argument('path', options_list=['--path'],
                   help='Directory to place the package contents.')
        c.argument('file_filter', options_list=['--file-filter'],
                   help='Wildcard filter for file download.')
        c.argument('no_hardlinks', options_list=['--no-hardlinks'],
                   action='store_true',
                   help='Disable the use of hard links when downloading. Use this option on file '
                        'systems that do not support hard linking (e.g. some network shares, '
                        'containers, or virtual file systems).')

    with self.argument_context('artifacts universal publish') as c:
        c.argument('path', options_list=['--path'],
                   help='Directory containing the package contents.')
        c.argument('description', options_list=['--description', '-d'],
                   help='Description of the package.')
