import re

from decimal import Decimal
from pycomposefile.compose_element import ComposeElement, ComposeListOrMapElement, ComposeByteValue


class ResourceDetails(ComposeElement):
    element_keys = {
        "cpus": (Decimal, ""),
        "memory": (ComposeByteValue, ""),
        "pids": (int,
                 "https://github.com/compose-spec/compose-spec/blob/master/deploy.md#pids"),
        "devices": (None,
                    "https://github.com/compose-spec/compose-spec/blob/master/deploy.md#devices"),
    }


class Resources(ComposeElement):
    element_keys = {
        "limits": (ResourceDetails.from_parsed_yaml, ""),
        "reservations": (ResourceDetails.from_parsed_yaml, ""),
    }


class Placement(ComposeElement):
    element_keys = {
        "constraints": (ComposeListOrMapElement, "https://github.com/compose-spec/compose-spec/blob/master/deploy.md#constraints"),
        "preferences": (ComposeListOrMapElement, "https://github.com/compose-spec/compose-spec/blob/master/deploy.md#preferences"),
    }


class DeployTimespan(str):

    @classmethod
    def from_parsed_str(cls, value):
        timespan_validator = re.compile(r"\d+(ns|us|ms|s|m|h)")
        if not timespan_validator.match(value):
            # Should this default like it is currently or should it raise an error?
            value = "0s"
        return cls(value)


class UpdateConfig(ComposeElement):
    element_keys = {
        "parallelism": (int, ""),
        "delay": (DeployTimespan.from_parsed_str, ""),
        "failure_action": ((str, ["continue", "pause", "rollback"]), ""),
        "monitor": (DeployTimespan.from_parsed_str, ""),
        # TODO: find an example, not sure what this value looks like
        #  https://github.com/compose-spec/compose-spec/blob/master/deploy.md#update_config
        "max_failure_ratio": (str, ""),
        "order": ((str, ["stop-first", "start-first"]), ""),
    }


class Deploy(ComposeElement):
    element_keys = {
        "endpoint_mode": ((str, ["vip", "dnsrr"]), ""),
        "labels": (ComposeListOrMapElement, ""),
        "mode": ((str, ["global", "replicated"]), ""),
        "replicas": (int, ""),
        "resources": (Resources.from_parsed_yaml, ""),
        "rollback_config": (UpdateConfig.from_parsed_yaml, ""),
        "update_config": (UpdateConfig.from_parsed_yaml, ""),
        "placement": (Placement.from_parsed_yaml,
                      "https://github.com/compose-spec/compose-spec/blob/master/deploy.md#placement"),
        "restart_policy": (None,
                           "https://github.com/compose-spec/compose-spec/blob/master/deploy.md#restart_policy"),
    }
