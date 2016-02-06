import logging

from azure.cli.main import RC

def add_commands(create_parser):
    from .storage import add_storage_commands
    storage_parser = create_parser(RC.STORAGE_COMMAND, help=RC.STORAGE_COMMAND_HELP)
    storage_commands = storage_parser.add_subparsers(dest='command')
    add_storage_commands(storage_commands.add_parser)

def process_command(args):
    if args.service == 'storage':
        import azure.cli.commands.storage as cmd
    elif args.service == 'spam':
        import azure.cli.commands.spam as cmd
    else:
        logging.error(RC.UNKNOWN_SERVICE.format(args.service))
        return
    
    try:
        func = getattr(cmd, args.command.lower())
    except AttributeError:
        logging.error(RC.UNKNOWN_COMMAND.format(args.service, args.command))
        return
    
    func(args)
