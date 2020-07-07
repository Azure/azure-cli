from tox.config.cli.parser import ToxParser


def env_run_create_flags(parser: ToxParser):
    parser.add_argument(
        "-r", "--recreate", dest="recreate", help="recreate the tox environments", action="store_true",
    )
    parser.add_argument("-n", "--notest", dest="no_test", help="do not run the test commands", action="store_true")
