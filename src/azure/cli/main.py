import os
import sys

from .application import Application, Configuration

from ._logging import configure_logging, logger
from ._session import Session
from ._output import OutputProducer

# CONFIG provides external configuration options
CONFIG = Session()

# SESSION provides read-write session variables
SESSION = Session()

def main(args, file=sys.stdout): #pylint: disable=redefined-builtin
    CONFIG.load(os.path.expanduser('~/az.json'))
    SESSION.load(os.path.expanduser('~/az.sess'), max_age=3600)

    configure_logging(args, CONFIG)

    from ._locale import install as locale_install
    locale_install(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                'locale',
                                CONFIG.get('locale', 'en-US')))

    config = Configuration(args)
    app = Application(config)
    app.load_commands()
    try:
        cmd_result = app.execute(args)
        # Commands can return a dictionary/list of results
        # If they do, we print the results.
        if cmd_result:
            formatter = OutputProducer.get_formatter(app.configuration.output_format)
            OutputProducer(formatter=formatter, file=file).out(cmd_result)
    except RuntimeError as ex:
        logger.error(ex.args[0])
        return ex.args[1] if len(ex.args) >= 2 else -1
    except KeyboardInterrupt:
        return -1

