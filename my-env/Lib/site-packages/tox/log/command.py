class CommandLog:
    """Report commands interacting with third party tools"""

    def __init__(self, container):
        self.entries = container

    def add_command(self, argv, output, error, retcode):
        data = {"command": argv, "output": output, "retcode": retcode, "error": error}
        self.entries.append(data)
        return data
