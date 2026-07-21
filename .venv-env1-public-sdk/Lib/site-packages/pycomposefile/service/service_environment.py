from pycomposefile.compose_element import ComposeListOrMapElement, ComposeStringOrListElement


class Environment(ComposeListOrMapElement):
    pass


class EnvFile(ComposeStringOrListElement):

    def readFile(self):
        env_array = []

        for file_name in self:
            f = open(file_name)

            for line in f.readlines():
                if not line.startswith("#"):
                    env_array.append(line.rstrip("\n"))
            f.close()
        return Environment(env_array)
