from decimal import Decimal


from pycomposefile.service.service_misc import (Expose,
                                                DependsOn,
                                                StorageOpt,
                                                Ulimits)
from pycomposefile.service.service_blkio_config import BlkioConfig
from pycomposefile.service.service_build import Build
from pycomposefile.service.service_deploy import Deploy
from pycomposefile.service.service_credential_spec import CredentialSpec
from pycomposefile.service.service_cap import Cap
from pycomposefile.service.service_configs import (Configs, Secrets)
from pycomposefile.service.service_command import Command
from pycomposefile.service.service_environment import (Environment, EnvFile)
from pycomposefile.service.service_healthcheck import HealthCheck
from pycomposefile.service.service_logging import Logging
from pycomposefile.service.service_networks import Networks
from pycomposefile.service.service_ports import Ports
from pycomposefile.service.service_volumes import Volumes
from pycomposefile.compose_element import (ComposeElement,
                                           ComposeListOrMapElement,
                                           ComposeByteValue,
                                           ComposeStringOrListElement)


class Service(ComposeElement):
    element_keys = {
        "image": (str, ""),
        "build": (Build,
                  "https://github.com/compose-spec/compose-spec/blob/master/build.md"),
        "container_name": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#container_name"),
        "cpu_count": (Decimal, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#cpu_count"),
        "entrypoint": (Command, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#entrypoint"),
        "command": (Command, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#command"),
        "deploy": (Deploy.from_parsed_yaml, "https://github.com/compose-spec/compose-spec/blob/master/deploy.md"),
        "expose": (Expose, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#expose"),
        "ports": (Ports, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#long-syntax-2"),
        "cpus": (Decimal, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#cpus"),
        "credential_spec": (CredentialSpec.from_parsed_yaml, ""),
        "blkio_config": (BlkioConfig.from_parsed_yaml,
                         "https://github.com/compose-spec/compose-spec/blob/master/spec.md#blkio_config"),
        "cpu_percent": (Decimal,
                        "https://github.com/compose-spec/compose-spec/blob/master/spec.md#cpu_percent"),
        "cpu_shares": (int,
                       "https://github.com/compose-spec/compose-spec/blob/master/spec.md#cpu_shares"),
        "cpu_period": (str,

                       "https://github.com/compose-spec/compose-spec/blob/master/spec.md#cpu_period"),
        "cpu_quota": (int,
                      "https://github.com/compose-spec/compose-spec/blob/master/spec.md#cpu_quota"),
        "cpu_rt_runtime": (str,
                           "https://github.com/compose-spec/compose-spec/blob/master/spec.md#cpu_rt_runtime"),
        "cpu_rt_period": (str,
                          "https://github.com/compose-spec/compose-spec/blob/master/spec.md#cpu_rt_period"),
        "cpuset": (ComposeStringOrListElement,
                   "https://github.com/compose-spec/compose-spec/blob/master/spec.md#cpuset"),

        "cap_add": (Cap,
                    "https://github.com/compose-spec/compose-spec/blob/master/spec.md#cap_add"),
        "cap_drop": (Cap,
                     "https://github.com/compose-spec/compose-spec/blob/master/spec.md#cap_add"),
        "cgroup_parent": (str,
                          "https://github.com/compose-spec/compose-spec/blob/master/spec.md#cgroup_parent"),
        "configs": (Configs,
                    "https://github.com/compose-spec/compose-spec/blob/master/spec.md#configs"),
        "depends_on": (DependsOn, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#depends_on"),
        "env_file": (EnvFile, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#env_file"),
        "environment": (Environment, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#environment"),
        "mem_reservation": (ComposeByteValue, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#mem_reservation"),
        "secrets": (Secrets, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#secrets"),
        "scale": (int, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#scale"),
        "device_cgroup_rules": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#device_cgroup_rules"),
        "devices": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#devices"),
        "dns": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#dns"),
        "dns_opt": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#dns_opt"),
        "dns_search": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#dns_search"),
        "domainname": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#domainname"),
        "external_links": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#external_links"),
        "extra_hosts": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#extra_hosts"),
        "group_add": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#group_add"),
        "healthcheck": (HealthCheck.from_parsed_yaml, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#healthcheck"),
        "hostname": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#hostname"),
        "init": (bool, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#init"),
        "ipc": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#ipc"),
        "isolation": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#isolation"),
        "labels": (ComposeListOrMapElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#labels"),
        "links": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#links"),
        "logging": (Logging, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#logging"),
        "network_mode": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#network_mode"),
        "networks": (Networks, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#networks"),
        "mac_address": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#mac_address"),
        "mem_limit": (ComposeByteValue, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#mem_limit"),
        "mem_swappiness": ((int, [0, 100]), "https://github.com/compose-spec/compose-spec/blob/master/spec.md#mem_swappiness"),
        "memswap_limit": (ComposeByteValue, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#memswap_limit"),
        "oom_kill_disable": (bool, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#oom_kill_disable"),
        "oom_score_adj": ((int, [-1000, 1000]), "https://github.com/compose-spec/compose-spec/blob/master/spec.md#oom_score_adj"),
        "pid": (int, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#pid"),
        "pids_limit": (int, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#pids_limit"),
        "platform": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#platform"),
        "privileged": (bool, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#privileged"),
        "profiles": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#profiles"),
        "pull_policy": ((str, ["always", "never", "missing", "build"]), "https://github.com/compose-spec/compose-spec/blob/master/spec.md#pull_policy"),
        "read_only": (bool, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#read_only"),
        "restart": ((str, ["no", "always", "on-failure", "unless-stopped"]), "https://github.com/compose-spec/compose-spec/blob/master/spec.md#restart"),
        "runtime": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#runtime"),
        "security_opt": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#security_opt"),
        "shm_size": (ComposeByteValue, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#shm_size"),
        "stdin_open": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#stdin_open"),
        "stop_grace_period": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#stop_grace_period"),
        "stop_signal": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#stop_signal"),
        "storage_opt": (StorageOpt.from_parsed_yaml, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#storage_opt"),
        "sysctls": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#sysctls"),
        "tmpfs": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#tmpfs"),
        "tty": (bool, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#tty"),
        "ulimits": (Ulimits.from_parsed_yaml, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#ulimits"),
        "user": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#user"),
        "userns_mode": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#userns_mode"),
        "volumes": (Volumes, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#volumes"),
        "volumes_from": (ComposeStringOrListElement, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#volumes_from"),
        "working_dir": (str, "https://github.com/compose-spec/compose-spec/blob/master/spec.md#working_dir")

    }

    def entrypoint_and_command(self):
        if self.command is None and self.entrypoint is None:
            return None
        else:
            container_entrypoint_and_command = ""
            if self.entrypoint is not None:
                container_entrypoint_and_command += self.entrypoint.command_string()
                container_entrypoint_and_command += " "
            if self.command is not None:
                container_entrypoint_and_command += self.command.command_string()
            return container_entrypoint_and_command

    def resolve_environment_hierarchy(self):
        if self.env_file is not None:
            env_file = self.env_file.readFile()
            env_file.update(self.environment or [])
            return env_file
        else:
            return self.environment
