import argparse
import collections
from azure.cli.commands import computed_value

def register(application):
    def split_id(source, target):
        def split(namespace):
            try:
                id = getattr(namespace, source)
                parts = id.split('/')
                setattr(namespace, target, parts[8])
                setattr(namespace, source, parts[4])
            except Exception:
                raise RuntimeError(
                    'Invalid RESOURCEID "{0}". You have to specify a RESOURCEGROUP and NAME or a valid RESOURCEID'.format(id))
        return split

    def annotate_id(command_table):
        for command in command_table.values():
            arguments = command['arguments']
            rg_name = {arg['_semantic_type']: arg
                       for arg in arguments
                       if arg.get('_semantic_type', None) in ('resource_group_name',
                                                              'resource_name')}
            try:
                rg = rg_name['resource_group_name']
                name = rg_name['resource_name']
                arguments.remove(rg)
                arguments.remove(name)
                name_dest = name.get('dest') or name.get('name').split()[0].replace('--', '', 1).replace('-', '_')
                arguments.extend((
                    {
                        'name': rg.get('dest', 'resource_group_name'),
                        'metavar': '(RESOURCEID | %s %s)' % (rg.get('metavar', 'RESOURCEGROUP'),
                                                             name.get('metavar', 'NAME')),
                        'help': 'Resource ID or resource group name followed by resource name',
                    },
                    {
                        'name': name_dest,
                        'help': argparse.SUPPRESS,
                        'default': computed_value(
                            split_id(
                                rg.get('dest', 'resource_group_name'),
                                name.get('dest'))),
                        'nargs': '?'
                    }))
            except KeyError:
                pass

    def validate_resourcegroup_name(args):
        for name in dir(args):
            if not name.startswith('_') and name != 'func' and callable(getattr(args, name, None)):
                getattr(args, name)(args)

    application.register(application.COMMAND_TABLE_LOADED, annotate_id)

