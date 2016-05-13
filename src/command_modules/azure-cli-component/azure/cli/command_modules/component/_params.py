from azure.cli._locale import L

# BASIC PARAMETER CONFIGURATION

PARAMETER_ALIASES = {
    'component_name': {
        'name': '--name -n',
        'help': L('Name of component'),
        'choices': ['component', 'network', 'profile', 'resource',
                    'role', 'storage', 'taskhelp', 'vm']
    },
    'force': {
        'name': '--force -f',
        'help': L('Suppress delete confirmation prompt'),
        'action': 'store_true'
    },
    'link': {
        'name': '--link -l',
        'help': L('If a url or path to an html file, the parse for links to archives. If local ' + \
                  'path or file:// url that\'s a directory, then look for archives in the ' + \
                  'directory listing.')
    },
    'private': {
        'name': '--private -p',
        'action': 'store_true',
        'help': L('Get from the project PyPI server')
    },
    'version': {
        'name': '--version',
        'help': L('Component version (otherwise latest)')
    }
}
