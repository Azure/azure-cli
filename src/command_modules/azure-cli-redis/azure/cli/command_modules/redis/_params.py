# pylint: disable=line-too-long
from azure.cli.commands.parameters import (get_resource_name_completion_list, name_type)
from azure.cli.commands import register_cli_argument, CliArgumentType
import azure.cli.commands.arm

class JsonString(dict):

    def __init__(self, value):
        import json
        if value[0] in ("'", '"') and value[-1] == value[0]:
            value = value[1:-1]
        try:
            print(value)
            dictval = json.loads(value)
            self.update(dictval)
        except Exception as ex:
            print(ex)

register_cli_argument('redis', 'name', arg_type=name_type, completer=get_resource_name_completion_list('Microsoft.Cache/redis'), id_part='name')
register_cli_argument('redis', 'redis_configuration', type=JsonString)
register_cli_argument('redis import-method', 'files', nargs='+')
