import argparse
from typing import List, Optional

from tox.config.cli.parser import ToxParser
from tox.config.source.ini import StrConvert


def env_list_flag(parser: ToxParser):
    class ToxEnvList(argparse.Action):
        # noinspection PyShadowingNames
        def __call__(self, parser, args, values, option_string=None):
            list_envs = StrConvert().to(values, of_type=List[str])
            setattr(args, self.dest, list_envs)

    parser.add_argument(
        "-e",
        dest="env",
        help="tox environment(s) to run",
        action=ToxEnvList,
        default=None,
        of_type=Optional[List[str]],
    )
