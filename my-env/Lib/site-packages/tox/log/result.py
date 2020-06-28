"""Generate json report of a run"""
import json
import socket
import sys

from tox.version import __version__

from .command import CommandLog
from .env import EnvLog


class ResultLog:
    """The result of a tox session"""

    def __init__(self):
        command_log = []
        self.command_log = CommandLog(command_log)
        self.content = {
            "reportversion": "1",
            "toxversion": __version__,
            "platform": sys.platform,
            "host": socket.getfqdn(),
            "commands": command_log,
        }

    @classmethod
    def from_json(cls, data):
        result = cls()
        result.content = json.loads(data)
        result.command_log = CommandLog(result.content["commands"])
        return result

    def get_envlog(self, name):
        """Return the env log of a environment (create on first call)"""
        test_envs = self.content.setdefault("testenvs", {})
        env_data = test_envs.setdefault(name, {})
        return EnvLog(self, name, env_data)

    def dumps_json(self):
        """Return the json dump of the current state, indented"""
        return json.dumps(self.content, indent=2)
