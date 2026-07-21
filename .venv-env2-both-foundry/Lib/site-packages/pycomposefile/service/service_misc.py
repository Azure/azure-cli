from pycomposefile.compose_element import (ComposeElement,
                                           ComposeByteValue,
                                           ComposeStringOrListElement)


class Expose(ComposeStringOrListElement):
    transform = int


class Dependency(str):
    def __new__(cls, config, key=None, compose_path=None, ) -> None:
        condition = None
        if isinstance(config, Dependency):
            return config
        if isinstance(config, tuple):
            name, detail = config
            condition = detail["condition"]
        else:
            name = config
        ob = super().__new__(cls, name)
        ob.__setattr__('condition', condition)
        return ob


class DependsOn(ComposeStringOrListElement):
    def __init__(self, config, key=None, compose_path=None):
        self.transform = Dependency
        if isinstance(config, dict):
            config_to_list = []
            for key in config.keys():
                config_to_list.append((key, config[key]))
            config = config_to_list
        super().__init__(config, key, compose_path)


class StorageOpt(ComposeElement):
    element_keys = {
        "size": (ComposeByteValue, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#storage_opt")
    }


class Nofile(ComposeElement):
    element_keys = {
        "hard": (int, ""),
        "soft": (int, ""),
    }


class Ulimits(ComposeElement):
    element_keys = {
        "nproc": (int, ""),
        "nofile": (Nofile.from_parsed_yaml, "")
    }

    @classmethod
    def from_parsed_yaml(cls, config, name, compose_path):
        if config is None:
            return None
        if isinstance(config, str) or isinstance(config, int):
            new_dict = {}
            new_dict["nproc"] = config
            config = new_dict
        compose_path = f"{compose_path}/{name}"
        return cls(config, compose_path)
