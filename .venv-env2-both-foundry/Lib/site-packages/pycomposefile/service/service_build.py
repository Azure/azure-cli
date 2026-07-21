from pycomposefile.compose_element import ComposeElement, ComposeByteValue, ComposeStringOrListElement, ComposeListOrMapElement
from pycomposefile.service.service_environment import Environment
from pycomposefile.service.service_configs import Secrets


class Build(ComposeElement):
    element_keys = {
        "context": (str, "https://github.com/compose-spec/compose-spec/blob/master/build.md#context-required"),
        "dockerfile": (str, "https://github.com/compose-spec/compose-spec/blob/master/build.md#dockerfile"),
        "args": (Environment, "https://github.com/compose-spec/compose-spec/blob/master/build.md#args"),
        "ssh": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/build.md#ssh"),
        "cache_from": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/build.md#cache_from"),
        "cache_to": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/build.md#cache_to"),
        "extra_hosts": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/build.md#extra_hosts"),
        "isolation": (str, "https://github.com/compose-spec/compose-spec/blob/master/build.md#isolation"),
        "labels": (ComposeListOrMapElement, "https://github.com/compose-spec/compose-spec/blob/master/build.md#labels"),
        "no_cache": (bool, "https://github.com/compose-spec/compose-spec/blob/master/build.md#no_cache"),
        "pull": (bool, "https://github.com/compose-spec/compose-spec/blob/master/build.md#pull"),
        "shm_size": (ComposeByteValue, "https://github.com/compose-spec/compose-spec/blob/master/build.md#shm_size"),
        "target": (str, "https://github.com/compose-spec/compose-spec/blob/master/build.md#target"),
        "secrets": (Secrets, "https://github.com/compose-spec/compose-spec/blob/master/build.md#secrets"),
        "tags": (ComposeListOrMapElement, "https://github.com/compose-spec/compose-spec/blob/master/build.md#tags")
    }

    def __init__(self, config, key=None, compose_path=""):
        if isinstance(config, str):
            config = {
                "context": config
            }
        super().__init__(config, compose_path)
