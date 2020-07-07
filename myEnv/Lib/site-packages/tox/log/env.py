from copy import copy

from .command import CommandLog


class EnvLog:
    """Report the status of a tox environment"""

    def __init__(self, result_log, name, content):
        self.reportlog = result_log
        self.name = name
        self.content = content

    def set_python_info(self, python_info):
        answer = copy(python_info.__dict__)
        answer["executable"] = python_info.executable
        self.content["python"] = answer

    def get_commandlog(self, name):
        """get the command log for a given group name"""
        return CommandLog(self)

    def set_installed(self, packages):
        self.content["installed_packages"] = packages

    def set_header(self, installpkg):
        """
        :param py.path.local installpkg: Path ot the package.
        """
        self.dict["installpkg"] = {
            "sha256": installpkg.computehash("sha256"),
            "basename": installpkg.basename,
        }
