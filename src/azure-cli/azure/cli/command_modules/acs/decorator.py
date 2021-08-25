# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from knack.log import get_logger
from typing import Any, List, Dict, Union

from azure.cli.core import AzCommandsLoader
from azure.cli.core.azclierror import (
    CLIInternalError,
    MutuallyExclusiveArgumentError,
)
from azure.cli.core.commands import AzCliCommand
from azure.cli.core.profiles import ResourceType

from .custom import (
    _get_rg_location,
    _validate_ssh_key,
    _get_default_dns_prefix,
    _set_vm_set_type,
    set_load_balancer_sku,
    get_subscription_id,
)

logger = get_logger(__name__)


def safe_list_get(li: List, idx: int, default: Any = None):
    # Attempt to get the element with index `idx` from an object `li` (which should be a `list`),
    # if the index is invalid (like out of range), return `default` (whose default value is `None`)
    if isinstance(li, list):
        try:
            return li[idx]
        except IndexError:
            return default
    return None


# pylint: disable=too-many-instance-attributes,too-few-public-methods
class AKSCreateModels:
    # Used to store models (i.e. the corresponding class of a certain api version specified by `resource_type`)
    # which would be used during the creation process.
    def __init__(
        self,
        cmd: AzCommandsLoader,
        resource_type: ResourceType = ResourceType.MGMT_CONTAINERSERVICE,
    ):
        self.__cmd = cmd
        self.resource_type = resource_type
        self.ManagedClusterWindowsProfile = self.__cmd.get_models(
            "ManagedClusterWindowsProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedClusterSKU = self.__cmd.get_models(
            "ManagedClusterSKU",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ContainerServiceNetworkProfile = self.__cmd.get_models(
            "ContainerServiceNetworkProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ContainerServiceLinuxProfile = self.__cmd.get_models(
            "ContainerServiceLinuxProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedClusterServicePrincipalProfile = self.__cmd.get_models(
            "ManagedClusterServicePrincipalProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ContainerServiceSshConfiguration = self.__cmd.get_models(
            "ContainerServiceSshConfiguration",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ContainerServiceSshPublicKey = self.__cmd.get_models(
            "ContainerServiceSshPublicKey",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedClusterAADProfile = self.__cmd.get_models(
            "ManagedClusterAADProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedClusterAutoUpgradeProfile = self.__cmd.get_models(
            "ManagedClusterAutoUpgradeProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedClusterAgentPoolProfile = self.__cmd.get_models(
            "ManagedClusterAgentPoolProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedClusterIdentity = self.__cmd.get_models(
            "ManagedClusterIdentity",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.UserAssignedIdentity = self.__cmd.get_models(
            "UserAssignedIdentity",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedCluster = self.__cmd.get_models(
            "ManagedCluster",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ManagedServiceIdentityUserAssignedIdentitiesValue = (
            self.__cmd.get_models(
                "ManagedServiceIdentityUserAssignedIdentitiesValue",
                resource_type=self.resource_type,
                operation_group="managed_clusters",
            )
        )
        self.ExtendedLocation = self.__cmd.get_models(
            "ExtendedLocation",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        self.ExtendedLocationTypes = self.__cmd.get_models(
            "ExtendedLocationTypes",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )
        # not directly used
        self.ManagedClusterAPIServerAccessProfile = self.__cmd.get_models(
            "ManagedClusterAPIServerAccessProfile",
            resource_type=self.resource_type,
            operation_group="managed_clusters",
        )


# pylint: disable=too-many-public-methods
class AKSCreateContext:
    # Used to store intermediate variables (usually this stores the dynamically completed value of the parameter,
    # which has not been decorated into the `mc` object, and some pure intermediate variables (such as the
    # subscription ID)) and a copy of the original function parameters, and provide "getter" methods for all
    # parameters.
    # To dynamically complete a parameter or check the validity of a parameter, please provide a "getter" function
    # named `get_xxx`, where `xxx` is the parameter name. In this function, the process of obtaining parameter
    # values, dynamic completion (optional), and validation (optional) should be followed. The obtaining of
    # parameter values should further follow the order of obtaining from the `mc` object, from the intermediates,
    # or from the original value.
    # Note: Dynamic completion will also perform some operations that regulate parameter values, such as
    # converting int 0 to None.
    # Attention: In case of checking the validity of parameters, be sure not to set the `enable_validation` to
    # `True` to avoid loop calls, when using the getter function to obtain the value of other parameters.
    # Attention: After the parameter is dynamically completed, it must be added to the intermediates; and after
    # the parameter is decorated into the `mc` object, the corresponding intermediate should be deleted.
    # Attention: One of the most basic principles is that when the parameter/profile is decorated into the `mc`
    # object, it should never be modified, only read-only operations (e.g. validation) can be performed.
    def __init__(self, cmd: AzCliCommand, raw_parameters: Dict):
        self.cmd = cmd
        self.raw_param = raw_parameters
        self.intermediates = dict()
        self.mc = None

    def attach_mc(self, mc):
        if self.mc is None:
            self.mc = mc
        else:
            msg = "the same" if self.mc == mc else "different"
            raise CLIInternalError(
                "Attempting to attach the `mc` object again, the two objects are {}.".format(
                    msg
                )
            )

    def get_intermediate(self, variable_name: str, default_value: Any = None):
        if variable_name not in self.intermediates:
            msg = "The intermediate '{}' does not exist, return default value '{}'.".format(
                variable_name, default_value
            )
            logger.debug(msg)
        return self.intermediates.get(variable_name, default_value)

    def set_intermediate(
        self, variable_name: str, value: Any, overwrite_exists: bool = False
    ):
        if variable_name in self.intermediates:
            if overwrite_exists:
                msg = "The intermediate '{}' is overwritten. Original value: '{}', new value: '{}'.".format(
                    variable_name, self.intermediates.get(variable_name), value
                )
                logger.debug(msg)
                self.intermediates[variable_name] = value
            elif self.intermediates.get(variable_name) != value:
                msg = "The intermediate '{}' already exists, but overwrite is not enabled." \
                    "Original value: '{}', candidate value: '{}'.".format(
                        variable_name,
                        self.intermediates.get(variable_name),
                        value,
                    )
                # warning level log will be output to the console, which may cause confusion to users
                logger.warning(msg)
        else:
            self.intermediates[variable_name] = value

    def remove_intermediate(self, variable_name: str):
        self.intermediates.pop(variable_name, None)

    # pylint: disable=unused-argument
    def get_resource_group_name(
        self, enable_validation: bool = False, **kwargs
    ):
        # Note: This parameter will not be decorated into the `mc` object.
        # read the original value passed by the command
        resource_group_name = self.raw_param.get("resource_group_name")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return resource_group_name

    # pylint: disable=unused-argument
    def get_name(self, enable_validation: bool = False, **kwargs):
        # Note: This parameter will not be decorated into the `mc` object.
        # read the original value passed by the command
        name = self.raw_param.get("name")

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return name

    # pylint: disable=unused-argument
    def get_ssh_key_value(self, enable_validation: bool = False, **kwargs):
        # read the original value passed by the command
        raw_value = self.raw_param.get("ssh_key_value")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if (
            self.mc and
            self.mc.linux_profile and
            self.mc.linux_profile.ssh and
            self.mc.linux_profile.ssh.public_keys
        ):
            public_key_obj = safe_list_get(
                self.mc.linux_profile.ssh.public_keys, 0, None
            )
            if public_key_obj:
                mc_property = public_key_obj.key_data

        # set defautl value
        if mc_property is not None:
            ssh_key_value = mc_property
        else:
            ssh_key_value = raw_value

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            _validate_ssh_key(
                no_ssh_key=self.get_no_ssh_key(), ssh_key_value=ssh_key_value
            )
        return ssh_key_value

    # pylint: disable=unused-argument
    def get_dns_name_prefix(self, enable_validation: bool = False, **kwargs):
        parameter_name = "dns_name_prefix"

        # read the original value passed by the command
        raw_value = self.raw_param.get(parameter_name)
        # Try to read from intermediates, the intermediate only exists when the parameter value has been
        # dynamically completed but has not been decorated into the `mc` object.
        # Note: The intermediate value should be cleared immediately after it is decorated into the
        # `mc` object.
        intermediate = self.get_intermediate(parameter_name, None)
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.dns_prefix:
            mc_property = self.mc.dns_prefix

        # set defautl value
        read_from_mc = False
        if mc_property is not None:
            dns_name_prefix = mc_property
            # clean up intermediate if `mc` has been decorated
            self.remove_intermediate(parameter_name)
            read_from_mc = True
        elif intermediate is not None:
            dns_name_prefix = intermediate
        else:
            dns_name_prefix = raw_value

        dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        if not dns_name_prefix and not self.get_fqdn_subdomain():
            dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        dynamic_completion = dynamic_completion and not read_from_mc
        # In case the user does not specify the parameter and it meets the conditions of automatic completion,
        # necessary information is dynamically completed.
        if dynamic_completion:
            dns_name_prefix = _get_default_dns_prefix(
                name=self.get_name(),
                resource_group_name=self.get_resource_group_name(),
                subscription_id=self.get_intermediate("subscription_id"),
            )
            # add to intermediate
            self.set_intermediate(
                parameter_name, dns_name_prefix, overwrite_exists=True
            )

        # validation
        if enable_validation:
            if dns_name_prefix and self.get_fqdn_subdomain():
                raise MutuallyExclusiveArgumentError(
                    "--dns-name-prefix and --fqdn-subdomain cannot be used at same time"
                )
        return dns_name_prefix

    # pylint: disable=unused-argument
    def get_location(self, enable_validation: bool = False, **kwargs):
        parameter_name = "location"

        # read the original value passed by the command
        raw_value = self.raw_param.get(parameter_name)
        # try to read from intermediates
        intermediate = self.get_intermediate(parameter_name, None)
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc:
            mc_property = self.mc.location

        # set defautl value
        read_from_mc = False
        if mc_property is not None:
            location = mc_property
            # clean up intermediate if `mc` has been decorated
            self.remove_intermediate(parameter_name)
            read_from_mc = True
        elif intermediate is not None:
            location = intermediate
        else:
            location = raw_value

        dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        if location is None:
            dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        dynamic_completion = dynamic_completion and not read_from_mc
        if dynamic_completion:
            location = _get_rg_location(
                self.cmd.cli_ctx, self.get_resource_group_name()
            )
            # add to intermediate
            self.set_intermediate(
                parameter_name, location, overwrite_exists=True
            )

        # this parameter does not need validation
        return location

    # pylint: disable=unused-argument
    def get_kubernetes_version(self, enable_validation: bool = False, **kwargs):
        # read the original value passed by the command
        raw_value = self.raw_param.get("kubernetes_version")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc:
            mc_property = self.mc.kubernetes_version

        # set defautl value
        if mc_property is not None:
            kubernetes_version = mc_property
        else:
            kubernetes_version = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return kubernetes_version

    # pylint: disable=unused-argument
    def get_no_ssh_key(self, enable_validation: bool = False, **kwargs):
        # Note: This parameter will not be decorated into the `mc` object.
        # read the original value passed by the command
        no_ssh_key = self.raw_param.get("no_ssh_key")

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            _validate_ssh_key(
                no_ssh_key=no_ssh_key, ssh_key_value=self.get_ssh_key_value()
            )
        return no_ssh_key

    # pylint: disable=unused-argument
    def get_vm_set_type(self, enable_validation: bool = False, **kwargs):
        parameter_name = "vm_set_type"

        # read the original value passed by the command
        raw_value = self.raw_param.get(parameter_name)
        # try to read from intermediates
        intermediate = self.get_intermediate(parameter_name, None)
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.type

        # set defautl value
        read_from_mc = False
        if mc_property is not None:
            vm_set_type = mc_property
            # clean up intermediate if `mc` has been decorated
            self.remove_intermediate(parameter_name)
            read_from_mc = True
        elif intermediate is not None:
            vm_set_type = intermediate
        else:
            vm_set_type = raw_value

        dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        if not vm_set_type:
            dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        dynamic_completion = dynamic_completion and not read_from_mc
        if dynamic_completion:
            vm_set_type = _set_vm_set_type(
                vm_set_type=vm_set_type,
                kubernetes_version=self.get_kubernetes_version(),
            )
            # add to intermediate
            self.set_intermediate(
                parameter_name, vm_set_type, overwrite_exists=True
            )

        # this parameter does not need validation
        return vm_set_type

    # pylint: disable=unused-argument
    def get_load_balancer_sku(self, enable_validation: bool = False, **kwargs):
        parameter_name = "load_balancer_sku"

        # read the original value passed by the command
        raw_value = self.raw_param.get(parameter_name)
        # try to read from intermediates
        intermediate = self.get_intermediate(parameter_name, None)
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.network_profile:
            mc_property = self.mc.network_profile.load_balancer_sku

        # set defautl value
        read_from_mc = False
        if mc_property is not None:
            load_balancer_sku = mc_property
            # clean up intermediate if `mc` has been decorated
            self.remove_intermediate(parameter_name)
            read_from_mc = True
        elif intermediate is not None:
            load_balancer_sku = intermediate
        else:
            load_balancer_sku = raw_value

        dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        if not load_balancer_sku:
            dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        dynamic_completion = dynamic_completion and not read_from_mc
        if dynamic_completion:
            load_balancer_sku = set_load_balancer_sku(
                sku=load_balancer_sku,
                kubernetes_version=self.get_kubernetes_version(),
            )
            # add to intermediate
            self.set_intermediate(
                parameter_name, load_balancer_sku, overwrite_exists=True
            )

        # validation
        if enable_validation:
            if (
                load_balancer_sku == "basic" and
                self.get_api_server_authorized_ip_ranges()
            ):
                raise MutuallyExclusiveArgumentError(
                    "--api-server-authorized-ip-ranges can only be used with standard load balancer"
                )
        return load_balancer_sku

    # pylint: disable=unused-argument
    def get_api_server_authorized_ip_ranges(
        self, enable_validation: bool = False, **kwargs
    ):
        parameter_name = "api_server_authorized_ip_ranges"

        # read the original value passed by the command
        raw_value = self.raw_param.get(parameter_name)
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.api_server_access_profile:
            mc_property = self.mc.api_server_access_profile.authorized_ip_ranges

        # set defautl value
        if mc_property is not None:
            api_server_authorized_ip_ranges = mc_property
        else:
            api_server_authorized_ip_ranges = raw_value

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            if (
                api_server_authorized_ip_ranges and
                self.get_load_balancer_sku() == "basic"
            ):
                raise MutuallyExclusiveArgumentError(
                    "--api-server-authorized-ip-ranges can only be used with standard load balancer"
                )
        return api_server_authorized_ip_ranges

    # pylint: disable=unused-argument
    def get_fqdn_subdomain(self, enable_validation: bool = False, **kwargs):
        # read the original value passed by the command
        raw_value = self.raw_param.get("fqdn_subdomain")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc:
            mc_property = self.mc.fqdn_subdomain

        # set defautl value
        if mc_property is not None:
            fqdn_subdomain = mc_property
        else:
            fqdn_subdomain = raw_value

        # this parameter does not need dynamic completion

        # validation
        if enable_validation:
            if fqdn_subdomain and self.get_dns_name_prefix():
                raise MutuallyExclusiveArgumentError(
                    "--dns-name-prefix and --fqdn-subdomain cannot be used at same time"
                )
        return fqdn_subdomain

    # pylint: disable=unused-argument
    def get_nodepool_name(self, enable_validation: bool = False, **kwargs):
        parameter_name = "nodepool_name"

        # read the original value passed by the command
        raw_value = self.raw_param.get("nodepool_name")
        # try to read from intermediates
        intermediate = self.get_intermediate(parameter_name, None)
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.name

        # set defautl value
        read_from_mc = False
        if mc_property is not None:
            nodepool_name = mc_property
            # clean up intermediate if `mc` has been decorated
            self.remove_intermediate(parameter_name)
            read_from_mc = True
        elif intermediate is not None:
            nodepool_name = intermediate
        else:
            nodepool_name = raw_value

        dynamic_completion = False
        # check whether the parameter meet the conditions of dynamic completion
        if kwargs.get("enable_trim", False):
            dynamic_completion = True
        # disable dynamic completion if the value is read from `mc`
        dynamic_completion = dynamic_completion and not read_from_mc
        if dynamic_completion:
            if not nodepool_name:
                nodepool_name = "nodepool1"
            else:
                nodepool_name = nodepool_name[:12]
            # add to intermediate
            self.set_intermediate(
                parameter_name, nodepool_name, overwrite_exists=True
            )

        # this parameter does not need validation
        return nodepool_name

    # pylint: disable=unused-argument
    def get_nodepool_tags(self, enable_validation: bool = False, **kwargs):
        # read the original value passed by the command
        raw_value = self.raw_param.get("nodepool_tags")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.tags

        # set defautl value
        if mc_property is not None:
            nodepool_tags = mc_property
        else:
            nodepool_tags = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return nodepool_tags

    # pylint: disable=unused-argument
    def get_nodepool_labels(self, enable_validation: bool = False, **kwargs):
        # read the original value passed by the command
        raw_value = self.raw_param.get("nodepool_labels")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.node_labels

        # set defautl value
        if mc_property is not None:
            nodepool_labels = mc_property
        else:
            nodepool_labels = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return nodepool_labels

    # pylint: disable=unused-argument
    def get_node_count(self, enable_validation: bool = False, **kwargs) -> int:
        # read the original value passed by the command
        raw_value = self.raw_param.get("node_count")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.count

        # set defautl value
        if mc_property is not None:
            node_count = mc_property
        else:
            node_count = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return int(node_count)

    # pylint: disable=unused-argument
    def get_node_vm_size(self, enable_validation: bool = False, **kwargs):
        # read the original value passed by the command
        raw_value = self.raw_param.get("node_vm_size")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.vm_size

        # set defautl value
        if mc_property is not None:
            node_vm_size = mc_property
        else:
            node_vm_size = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_vm_size

    # pylint: disable=unused-argument
    def get_vnet_subnet_id(self, enable_validation: bool = False, **kwargs):
        # read the original value passed by the command
        raw_value = self.raw_param.get("vnet_subnet_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.vnet_subnet_id

        # set defautl value
        if mc_property is not None:
            vnet_subnet_id = mc_property
        else:
            vnet_subnet_id = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return vnet_subnet_id

    # pylint: disable=unused-argument
    def get_ppg(self, enable_validation: bool = False, **kwargs):
        # read the original value passed by the command
        raw_value = self.raw_param.get("ppg")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.proximity_placement_group_id

        # set defautl value
        if mc_property is not None:
            ppg = mc_property
        else:
            ppg = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return ppg

    # pylint: disable=unused-argument
    def get_zones(self, enable_validation: bool = False, **kwargs):
        # read the original value passed by the command
        raw_value = self.raw_param.get("zones")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.availability_zones

        # set defautl value
        if mc_property is not None:
            zones = mc_property
        else:
            zones = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return zones

    # pylint: disable=unused-argument
    def get_enable_node_public_ip(
        self, enable_validation: bool = False, **kwargs
    ):
        # read the original value passed by the command
        raw_value = self.raw_param.get("enable_node_public_ip")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.enable_node_public_ip

        # set defautl value
        if mc_property is not None:
            enable_node_public_ip = mc_property
        else:
            enable_node_public_ip = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_node_public_ip

    # pylint: disable=unused-argument
    def get_node_public_ip_prefix_id(
        self, enable_validation: bool = False, **kwargs
    ):
        # read the original value passed by the command
        raw_value = self.raw_param.get("node_public_ip_prefix_id")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.node_public_ip_prefix_id

        # set defautl value
        if mc_property is not None:
            node_public_ip_prefix_id = mc_property
        else:
            node_public_ip_prefix_id = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_public_ip_prefix_id

    # pylint: disable=unused-argument
    def get_enable_encryption_at_host(
        self, enable_validation: bool = False, **kwargs
    ):
        # read the original value passed by the command
        raw_value = self.raw_param.get("enable_encryption_at_host")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.enable_encryption_at_host

        # set defautl value
        if mc_property is not None:
            enable_encryption_at_host = mc_property
        else:
            enable_encryption_at_host = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_encryption_at_host

    # pylint: disable=unused-argument
    def get_enable_ultra_ssd(self, enable_validation: bool = False, **kwargs):
        # read the original value passed by the command
        raw_value = self.raw_param.get("enable_ultra_ssd")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.enable_ultra_ssd

        # set defautl value
        if mc_property is not None:
            enable_ultra_ssd = mc_property
        else:
            enable_ultra_ssd = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return enable_ultra_ssd

    # pylint: disable=unused-argument
    def get_max_pods(self, enable_validation: bool = False, **kwargs) -> Union[int, None]:
        # read the original value passed by the command
        raw_value = self.raw_param.get("max_pods")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.max_pods

        # set defautl value
        if mc_property is not None:
            max_pods = mc_property
        else:
            max_pods = raw_value
            # Note: 0 is converted to None
            if max_pods:
                max_pods = int(max_pods)
            else:
                max_pods = None

        # this parameter does not need validation
        return max_pods

    # pylint: disable=unused-argument
    def get_node_osdisk_size(self, enable_validation: bool = False, **kwargs) -> Union[int, None]:
        # read the original value passed by the command
        raw_value = self.raw_param.get("node_osdisk_size")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.os_disk_size_gb

        # set defautl value
        if mc_property is not None:
            node_osdisk_size = mc_property
        else:
            node_osdisk_size = raw_value
            # Note: 0 is converted to None
            if node_osdisk_size:
                node_osdisk_size = int(node_osdisk_size)
            else:
                node_osdisk_size = None

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_osdisk_size

    # pylint: disable=unused-argument
    def get_node_osdisk_type(self, enable_validation: bool = False, **kwargs):
        # read the original value passed by the command
        raw_value = self.raw_param.get("node_osdisk_type")
        # try to read the property value corresponding to the parameter from the `mc` object
        mc_property = None
        if self.mc and self.mc.agent_pool_profiles:
            agent_pool_profile = safe_list_get(
                self.mc.agent_pool_profiles, 0, None
            )
            if agent_pool_profile:
                mc_property = agent_pool_profile.os_disk_type

        # set defautl value
        if mc_property is not None:
            node_osdisk_type = mc_property
        else:
            node_osdisk_type = raw_value

        # this parameter does not need dynamic completion
        # this parameter does not need validation
        return node_osdisk_type


class AKSCreateDecorator:
    def __init__(
        self,
        cmd: AzCliCommand,
        client,
        models: AKSCreateModels,
        raw_parameters: Dict,
        resource_type: ResourceType = ResourceType.MGMT_CONTAINERSERVICE,
    ):
        self.cmd = cmd
        self.client = client
        self.models = models
        # store the context in the process of assemble the ManagedCluster object
        self.context = AKSCreateContext(cmd, raw_parameters)
        # `resource_type` is used to dynamically find the model (of a specific api version) provided by the
        # containerservice SDK, most models have been passed through the `modles` parameter (instantiatied
        # from `AKSCreateModels` (or `PreviewAKSCreateModels` in aks-preview), where resource_type (i.e.,
        # api version) has been specified), a very small number of models are instantiated through internal
        # functions, one use case is that `api_server_access_profile` is initialized by function
        # `_populate_api_server_access_profile` defined in `_helpers.py`
        self.resource_type = resource_type

    def init_mc(self):
        # get subscription id and store as intermediate
        subscription_id = get_subscription_id(self.cmd.cli_ctx)
        self.context.set_intermediate(
            "subscription_id", subscription_id, overwrite_exists=True
        )

        # initialize the `ManagedCluster` object with mandatory parameters (i.e. location)
        mc = self.models.ManagedCluster(location=self.context.get_location())
        return mc

    def set_up_agent_pool_profiles(self, mc):
        if not isinstance(mc, self.models.ManagedCluster):
            raise CLIInternalError(
                "Unexpected mc object with type '{}'.".format(type(mc))
            )

        agent_pool_profile = self.models.ManagedClusterAgentPoolProfile(
            # Must be 12 chars or less before ACS RP adds to it
            name=self.context.get_nodepool_name(enable_trim=True),
            tags=self.context.get_nodepool_tags(),
            node_labels=self.context.get_nodepool_labels(),
            count=self.context.get_node_count(),
            vm_size=self.context.get_node_vm_size(),
            os_type="Linux",
            vnet_subnet_id=self.context.get_vnet_subnet_id(),
            proximity_placement_group_id=self.context.get_ppg(),
            availability_zones=self.context.get_zones(),
            enable_node_public_ip=self.context.get_enable_node_public_ip(),
            node_public_ip_prefix_id=self.context.get_node_public_ip_prefix_id(),
            enable_encryption_at_host=self.context.get_enable_encryption_at_host(),
            enable_ultra_ssd=self.context.get_enable_ultra_ssd(),
            max_pods=self.context.get_max_pods(),
            type=self.context.get_vm_set_type(),
            mode="System",
            os_disk_size_gb=self.context.get_node_osdisk_size(),
            os_disk_type=self.context.get_node_osdisk_type(),
        )
        mc.agent_pool_profiles = [agent_pool_profile]
        return mc

    def construct_default_mc(self):
        # An all-in-one function used to create the complete `ManagedCluster` object, which will later be
        # passed as a parameter to the underlying SDK (mgmt-containerservice) to send the actual request.
        # Note: to reduce the risk of regression introduced by refactoring, this function is not complete
        # and is being implemented gradually.
        # initialize the `ManagedCluster` object
        mc = self.init_mc()
        # set up agent pool profile(s)
        mc = self.set_up_agent_pool_profiles(mc)
        return mc
