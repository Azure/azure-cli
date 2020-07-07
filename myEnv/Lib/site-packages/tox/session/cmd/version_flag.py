from pathlib import Path

from tox.config.cli.parser import ToxParser
from tox.plugin.impl import impl


@impl
def tox_add_option(parser: ToxParser):
    from tox.version import __version__
    import tox

    parser.add_argument(
        "--version", action="version", version="{} from {}".format(__version__, Path(tox.__file__).absolute()),
    )
