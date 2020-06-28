from typing import Dict, List, Optional, cast

from tox.config.main import Config
from tox.tox_env.runner import RunToxEnv


class State:
    def __init__(self, conf, tox_envs, opt_parse, args):
        self.conf = conf  # type:Config
        self.tox_envs = tox_envs  # type:Dict[str, RunToxEnv]
        options, unknown, handlers = opt_parse
        self.options = options
        self.unknown_options = unknown
        self.handlers = handlers
        self.args = args

    @property
    def env_list(self) -> List[str]:
        tox_env_keys = cast(Optional[List[str]], self.options.env)
        if tox_env_keys is None:
            tox_env_keys = cast(List[str], self.conf.core["env_list"])
        return tox_env_keys
