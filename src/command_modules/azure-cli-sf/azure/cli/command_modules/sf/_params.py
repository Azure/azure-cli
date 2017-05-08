# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from azure.cli.core.sdk.util import ParametersContext
from azure.cli.core.util import get_json_object


# Global parameters
# Documentation here can be omitted from command specification
with ParametersContext(command="sf") as c:
    c.argument("timeout", options_list=("--timeout", "-t"),
               type=int,
               help=("The server timeout for performing the operation, "
                     "specified in seconds. This is the maximum time a client "
                     "can wait."),
               default=60)

# Service commands
with ParametersContext(command="sf service create") as c:
    c.argument("named_scheme_list", type=get_json_object, default=None)
    c.argument("load_metrics", type=get_json_object, default=None)
    c.argument("placement_policy_list", type=get_json_object, default=None)
    c.argument("target_replica_set_size", type=int, default=None)
    c.argument("min_replica_set_size", type=int, default=None)
    c.argument("replica_restart_wait", type=int, default=None)
    c.argument("quorum_loss_wait", type=int, default=None)
    c.argument("stand_by_replica_keep", type=int, default=None)
    c.argument("instance_count", type=int, default=None)

with ParametersContext(command="sf service update") as c:
    c.argument("load_metrics", type=get_json_object, default=None)
    c.argument("placement_policy_list", type=get_json_object, default=None)
    c.argument("instance_count", type=int, default=None)
    c.argument("target_replica_set_size", type=int, default=None)
    c.argument("min_replica_set_size", type=int, default=None)

# Application commands
with ParametersContext(command="sf application create") as c:
    c.argument("parameters", type=get_json_object, default=None)
    c.argument("min_node_count", type=int, default=None)
    c.argument("max_node_count", type=int, default=None)
    c.argument("metrics", type=get_json_object, default=None)

with ParametersContext(command="sf application upgrade") as c:
    c.argument("parameters", type=get_json_object, default=None)
    c.argument("replica_set_check_timeout", type=int, default=42949672925)
    c.argument("max_unhealthy_apps", type=int, default=0)
    c.argument("default_service_health_policy", type=get_json_object,
               default=None)
    c.argument("service_health_policy", type=get_json_object, default=None)

# For some commands we take JSON strings as possible

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
