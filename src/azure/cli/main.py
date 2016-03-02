import os

from ._argparse import ArgumentParser
from ._logging import configure_logging, logger
from ._session import Session
from ._output import OutputProducer

# CONFIG provides external configuration options
CONFIG = Session()

# SESSION provides read-write session variables
SESSION = Session()

def main(args):
    CONFIG.load(os.path.expanduser('~/az.json'))
    SESSION.load(os.path.expanduser('~/az.sess'), max_age=3600)

    configure_logging(args, CONFIG)

    from ._locale import install as locale_install
    locale_install(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'locale',
                                CONFIG.get('locale', 'en-US')))


    parser = ArgumentParser("az")

    import azure.cli.commands as commands

    # Find the first noun on the command line and only load commands from that
    # module to improve startup time.
    for a in args:
        if not a.startswith('-'):
            commands.add_to_parser(parser, a)
            break
    else:
        # No noun found, so load all commands.
        commands.add_to_parser(parser)

    try:
        result = parser.execute(args)
        # Commands can return a dictionary/list of results
        # If they do, we print the results.
        if result:
            OutputProducer().out(result)
    except RuntimeError as ex:
        logger.error(ex.args[0])
        return ex.args[1] if len(ex.args) >= 2 else -1
    except KeyboardInterrupt:
        return -1
