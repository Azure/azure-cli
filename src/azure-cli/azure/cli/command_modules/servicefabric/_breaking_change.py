# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.breaking_change import register_argument_deprecate, register_required_flag_breaking_change

register_argument_deprecate(
    "az sf application update",
    "--service-type-policy",
    hide=True)
register_argument_deprecate(
    "az sf application update",
    "--upgrade-replica-set-check-timeout",
    hide=True)
register_argument_deprecate(
    "az sf application update",
    "--max-porcent-unhealthy-partitions",
    hide=True)
register_argument_deprecate(
    "az sf application update",
    "--max-porcent-unhealthy-replicas",
    hide=True)
register_argument_deprecate(
    "az sf application update",
    "--max-porcent-unhealthy-services",
    hide=True)
register_argument_deprecate(
    "az sf application update",
    "--max-porcent-unhealthy-apps",
    hide=True)
register_argument_deprecate(
    "az sf managed-application update",
    "--service-type-policy",
    hide=True)
register_argument_deprecate(
    "az sf managed-application update",
    "--upgrade-replica-set-check-timeout",
    hide=True)
register_argument_deprecate(
    "az sf managed-application update",
    "--instance-close-duration",
    hide=True)
register_argument_deprecate(
    "az sf managed-application update",
    "--consider-warning-as-error",
    hide=True)
register_argument_deprecate(
    "az sf managed-application update",
    "--max-percent-unhealthy-partitions",
    hide=True)
register_argument_deprecate(
    "az sf managed-application update",
    "--max-percent-unhealthy-replicas",
    hide=True)
register_argument_deprecate(
    "az sf managed-application update",
    "--max-percent-unhealthy-services",
    hide=True)
register_argument_deprecate(
    "az sf managed-application update",
    "--max-percent-unhealthy-deployed-applications",
    hide=True)
register_required_flag_breaking_change(
    "az sf managed-application-type version update",
    "--package-url"
)
