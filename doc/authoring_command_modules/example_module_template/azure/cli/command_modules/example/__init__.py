# Add command module logic to this package.

from azure.cli.commands import cli_command

def example(my_required_arg, my_optional_arg='MyDefault'):
    '''Returns the params you passed in.
    :param str my_required_arg: The argument that is required
    '''
    result = {'a': my_required_arg, 'b': my_optional_arg}
    return result

cli_command('example', example)
