from tox.config.cli.parser import ToxParser
from tox.plugin.impl import impl
from tox.session.state import State


@impl
def tox_add_option(parser: ToxParser):
    our = parser.add_command("list", ["l"], "list environments", list_env)
    our.add_argument("-d", action="store_true", help="list just default envs", dest="list_default_only")
    our.add_argument("-q", action="store_true", help="do not show description", dest="list_quiet")


def list_env(state: State):
    core = state.conf.core
    option = state.options

    default = core["env_list"]  # this should be something not affected by env-vars :-|
    ignore = {core["provision_tox_env"]}.union(default)
    extra = [] if option.list_default_only else [e for e in state.tox_envs.keys() if e not in ignore]

    if not option.list_quiet and default:
        print("default environments:")
    max_length = max(len(env) for env in (default.envs + extra))

    def report_env(name: str):
        if not option.list_quiet:
            text = state.tox_envs[name].conf["description"]
            if text is None:
                text = "[no description]"
            text = text.replace("\n", " ")
            msg = "{} -> {}".format(e.ljust(max_length), text).strip()
        else:
            msg = e
        print(msg)

    for e in default:
        report_env(e)
    if not option.list_default_only and extra:
        if not option.list_quiet:
            if default:
                print("")
            print("additional environments:")
        for e in extra:
            report_env(e)
