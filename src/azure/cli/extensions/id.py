import argparse
import collections

def register(application):
    def split_id(source, target):
        def split(namespace):
            try:
                id = getattr(namespace, source)
                parts = id.split('/')
                setattr(namespace, source, parts[4])
                setattr(namespace, target, parts[8])
            except Exception:
                raise RuntimeError('Invalid ID "{0}". You have to specify a valid ID or RESOURCEGROUP and NAME'.format(id))
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
                arguments.append({
                    'name': rg.get('dest', 'resource_group_name'),
                    'metavar': '(ID | %s %s)' % (rg.get('metavar', 'RESOURCEGROUP'), name.get('metavar', 'NAME')),
                    'help': 'Resource ID or resource group name followed by resource name',
                    })
                arguments.append({
                    'name': name.get('dest', 'name'),
                    'help': argparse.SUPPRESS,
                    'default': split_id(rg.get('dest', 'resource_group_name'), name.get('dest', 'name')),
                    'nargs': '?'
                    })
            except KeyError:
                pass

    def validate_resourcegroup_name(args):
        for name in dir(args):
            if not name.startswith('_') and name != 'func' and callable(getattr(args, name, None)):
                getattr(args, name)(args)

    application.register(application.COMMAND_TABLE_LOADED, annotate_id)
    application.register(application.COMMAND_PARSER_PARSED, validate_resourcegroup_name)

