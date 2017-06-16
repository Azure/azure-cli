# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.sdk.util import ParametersContext
from azure.cli.core.util import get_json_object

# For some commands we take JSON strings as possible
with ParametersContext(command="sf application create") as c:
    c.register("parameters", ("--parameters",), type=get_json_object,
               help="JSON encoded list of application parameters.")

with ParametersContext(command="sf application create") as c:
    c.register("metrics", ("--metrics",), type=get_json_object,
               help="JSON encoded list of application metrics and their \
               descriptions.")

with ParametersContext(command="sf application upgrade") as c:
    c.register("parameters", ("--parameters",), type=get_json_object,
               help="JSON encoded list of application parameter overrides to \
               be applied when upgrading an application. Note, when starting \
               an upgrade, be sure to include the existing application \
               parameters, if any.")

with ParametersContext(command="sf application upgrade") as c:
    c.register("default_service_health_policy",
               ("--default_service_health_policy",),
               type=get_json_object,
               help="JSON encoded specification of the health policy used by \
               default to evaluate the health of a service type.")

with ParametersContext(command="sf application upgrade") as c:
    c.register("service_health_policy", ("--service_health_policy",),
               type=get_json_object,
               help="JSON encoded map with service type health policy per \
               service type name. The map is empty be default.")

with ParametersContext(command="sf service create") as c:
    c.register("load_metrics", ("--load_metrics",),
               type=get_json_object,
               help="JSON encoded list of metrics used when load balancing \
               services across nodes.")

with ParametersContext(command="sf service create") as c:
    c.register("placement_policy_list", ("--placement_policy_list",),
               type=get_json_object,
               help="JSON encoded list of placement policies for the service, \
               and any associated domain names. Policies can be one or more \
               of: `NonPartiallyPlaceService`, `PreferPrimaryDomain`, \
               `RequireDomain`, `requireDomainDistribution`")

with ParametersContext(command="sf service update") as c:
    c.register("load_metrics", ("--load_metrics",),
               type=get_json_object,
               help="JSON encoded list of metrics used when load balancing \
               services across nodes.")

with ParametersContext(command="sf service update") as c:
    c.register("placement_policy_list", ("--placement_policy_list",),
               type=get_json_object,
               help="JSON encoded list of placement policies for the service, \
               and any associated domain names. Policies can be one or more \
               of: `NonPartiallyPlaceService`, `PreferPrimaryDomain`, \
               `RequireDomain`, `requireDomainDistribution`")

with ParametersContext(command="sf chaos start") as c:
    c.register("application_type_health_policy_map",
               ("--application_type_health_policy_map",),
               type=get_json_object,
               help="JSON encoded list with max percentage unhealthy \
               applications for specific application types. Each entry \
               specifies as a key the application type name and as  a value \
               an integer that represents the MaxPercentUnhealthyApplications \
               percentage used to evaluate the applications of the specified \
               application type.")

with ParametersContext(command="sf node service-package-upload") as c:
    c.register("share_policy",
               ("--share_policy",),
               type=get_json_object,
               help="JSON encoded list of sharing policies. Each sharing \
               policy element is composed of a 'name' and 'scope'. The name \
               corresponds to the name of the code, configuration, or data \
               package that is to be shared. The scope can either 'None', \
               'All', 'Code', 'Config' or 'Data'.")
