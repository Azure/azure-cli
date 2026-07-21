from pycomposefile.compose_element import ComposeElement, ComposeStringOrListElement


class Config(ComposeElement):
    element_keys = {
        "source": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#configs"),
        "target": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#configs"),
        "uid": (int, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#configs"),
        "gid": (int, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#configs"),
        "mode": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#configs"),
    }

    def __init__(self, config_definition, key=None, compose_path=""):
        if isinstance(config_definition, str):
            config_definition = {
                "source": config_definition
            }
        super().__init__(config_definition, compose_path)


class Configs(ComposeStringOrListElement):
    transform = Config


class Secrets(ComposeStringOrListElement):
    transform = Config
