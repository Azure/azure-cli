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

with ParametersContext(command="sf service resolve") as c:
    c.argument("partition_key_type", type=int, default=None)

with ParametersContext(command="sf service health") as c:
    c.argument("events_health_state_filter", type=int, default=None)
    c.argument("partitions_health_state_filter", type=int, default=None)

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

with ParametersContext(command="sf application health") as c:
    c.argument("events_health_state_filter", type=int, default=0)
    c.argument("deployed_applications_health_state_filter", type=int,
               default=0)
    c.argument("services_health_state_filter", type=int, default=0)

with ParametersContext(command="sf application type") as c:
    c.argument("max_results", type=int, default=None)

# Partition commands
with ParametersContext(command="sf partition health") as c:
    c.argument("events_health_state_filter", type=int, default=None)
    c.argument("replicas_health_state_filter", type=int, default=None)

# Replica commands
with ParametersContext(command="sf replica health") as c:
    c.argument("events_health_state_filter", type=int, default=None)

# Chaos commands
with ParametersContext(command="sf chaos start") as c:
    c.argument("max_cluster_stabilization", type=int, default=60)
    c.argument("max_concurrent_faults", type=int, default=1)
    c.argument("wait_time_between_faults", type=int, default=20)
    c.argument("wait_time_between_iterations", type=int, default=30)
    c.argument("max_percent_unhealthy_nodes", type=int, default=0)
    c.argument("max_percent_unhealthy_applications", type=int, default=0)
    c.argument("app_type_health_policy_map", type=get_json_object,
               default=None)

# Node commands
with ParametersContext(command="sf node service-package-upload") as c:
    c.argument("share_policy", type=get_json_object, default=None)

# Cluster commands
with ParametersContext(command="sf cluster health") as c:
    c.argument("nodes_health_state_filter", type=int, default=0)
    c.argument("applications_health_state_filter", type=int, default=0)
    c.argument("events_health_state_filter", type=int, default=0)

# Compose commands
with ParametersContext(command="sf compose list") as c:
    c.argument("max_results", type=int, default=None)
