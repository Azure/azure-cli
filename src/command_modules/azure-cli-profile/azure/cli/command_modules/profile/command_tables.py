from azure.cli.commands import CommandTable

COMMAND_TABLES = []

def generate_command_table():
    '''Combine the command tables to produce a single command table'''
    command_table = CommandTable()
    for ct in COMMAND_TABLES:
        command_table.update(ct)
    return command_table
