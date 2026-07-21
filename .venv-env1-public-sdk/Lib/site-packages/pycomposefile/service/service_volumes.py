from pycomposefile.compose_element import (ComposeElement,
                                           ComposeStringOrListElement,
                                           ComposeByteValue)


class Tmpfs(ComposeElement):
    element_keys = {
        "size": (ComposeByteValue, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4"),
        "mode": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4"),
    }


class Bind(ComposeElement):
    element_keys = {
        "propigation": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4"),
        "create_host_path": (bool, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4"),
        "selinux": ((str, ['z', 'Z']), "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4"),
    }


class Volume(ComposeElement):
    element_keys = {
        "nocopy": (bool, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4")
    }


class VolumeMap(ComposeElement):
    element_keys = {
        "type": ((str, ["volume", "bind", "tmpfs", "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4"]), "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4"),
        "source": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4"),
        "target": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4"),
        "volume": (Volume.from_parsed_yaml, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4"),
        "bind": (Bind.from_parsed_yaml, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4"),
        "read_only": (bool, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4"),
        "tmpfs": (Tmpfs.from_parsed_yaml, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4"),
        "consistency": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-4"),
    }

    @classmethod
    def from_parsed_yaml(cls, config, name=None, compose_path=None):
        if config is None:
            return None
        if isinstance(config, str):
            new_dict = {}
            split_string = config.split(":")
            if len(split_string) == 3:
                new_dict["source"], new_dict["target"], access_mode = split_string
                access_mode = access_mode.split(',')

                if 'rw' in access_mode:
                    new_dict["read_only"] = False
                elif "r" in access_mode:
                    new_dict["read_only"] = True

                if 'z' in access_mode:
                    bind = {}
                    bind["selinux"] = 'z'
                    new_dict["bind"] = bind
                elif 'Z' in access_mode:
                    bind = {}
                    bind["selinux"] = 'Z'
                    new_dict["bind"] = bind
            else:
                new_dict["source"], new_dict["target"] = split_string
            config = new_dict
        compose_path = f"{compose_path}/{name}"
        return cls(config, compose_path)


class Volumes(ComposeStringOrListElement):
    transform = VolumeMap.from_parsed_yaml
