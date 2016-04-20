import json
import sys

from azure.cli.application import Configuration

class Exporter(json.JSONEncoder):

    def default(self, o):#pylint: disable=method-hidden
        try:
            return super(Exporter, self).default(o)
        except TypeError:
            return str(o)

cmd_set_names = None
if len(sys.argv) > 1:
    cmd_set_names = sys.argv[1].split(',')

config = Configuration([])
cmd_table = config.get_command_table()
cmd_names = [x['name'] for x in cmd_table.values()
             if cmd_set_names is None or (x['name'].split()[0]) in cmd_set_names]

print('\n'.join(cmd_names))
