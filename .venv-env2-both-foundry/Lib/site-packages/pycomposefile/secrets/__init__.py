from pycomposefile.compose_element import ComposeElement


class SecretFile(str):
    def readFile(self):
        with open(self) as f:
            secret = f.read()
        return secret


class Secrets(ComposeElement):
    element_keys = {
        "name": (str, ""),
        "file": (SecretFile, ""),
        "external": (bool, ""),
    }
