# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
#
# Code generated by aaz-dev-tools
# --------------------------------------------------------------------------------------------

# pylint: skip-file
# flake8: noqa

from azure.cli.core.aaz import *


@register_command(
    "hdinsight-on-aks cluster upgrade list",
)
class List(AAZCommand):
    """List a cluster available upgrades.

    :example: List the cluster available upgrades.
        az hdinsight-on-aks cluster upgrade list -g {resourcesGroup} --cluster-pool-name {poolName} --cluster-name {clusterName}
    """

    _aaz_info = {
        "version": "2024-05-01",
        "resources": [
            ["mgmt-plane", "/subscriptions/{}/resourcegroups/{}/providers/microsoft.hdinsight/clusterpools/{}/clusters/{}/availableupgrades", "2024-05-01"],
        ]
    }

    AZ_SUPPORT_PAGINATION = True

    def _handler(self, command_args):
        super()._handler(command_args)
        return self.build_paging(self._execute_operations, self._output)

    _args_schema = None

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        if cls._args_schema is not None:
            return cls._args_schema
        cls._args_schema = super()._build_arguments_schema(*args, **kwargs)

        # define Arg Group ""

        _args_schema = cls._args_schema
        _args_schema.cluster_name = AAZStrArg(
            options=["--cluster-name"],
            help="The name of the HDInsight cluster.",
            required=True,
        )
        _args_schema.cluster_pool_name = AAZStrArg(
            options=["--cluster-pool-name"],
            help="The name of the cluster pool.",
            required=True,
        )
        _args_schema.resource_group = AAZResourceGroupNameArg(
            required=True,
        )
        return cls._args_schema

    def _execute_operations(self):
        self.pre_operations()
        self.ClusterAvailableUpgradesList(ctx=self.ctx)()
        self.post_operations()

    @register_callback
    def pre_operations(self):
        pass

    @register_callback
    def post_operations(self):
        pass

    def _output(self, *args, **kwargs):
        result = self.deserialize_output(self.ctx.vars.instance.value, client_flatten=True)
        next_link = self.deserialize_output(self.ctx.vars.instance.next_link)
        return result, next_link

    class ClusterAvailableUpgradesList(AAZHttpOperation):
        CLIENT_TYPE = "MgmtClient"

        def __call__(self, *args, **kwargs):
            request = self.make_request()
            session = self.client.send_request(request=request, stream=False, **kwargs)
            if session.http_response.status_code in [200]:
                return self.on_200(session)

            return self.on_error(session.http_response)

        @property
        def url(self):
            return self.client.format_url(
                "/subscriptions/{subscriptionId}/resourceGroups/{resourceGroupName}/providers/Microsoft.HDInsight/clusterpools/{clusterPoolName}/clusters/{clusterName}/availableUpgrades",
                **self.url_parameters
            )

        @property
        def method(self):
            return "GET"

        @property
        def error_format(self):
            return "MgmtErrorFormat"

        @property
        def url_parameters(self):
            parameters = {
                **self.serialize_url_param(
                    "clusterName", self.ctx.args.cluster_name,
                    required=True,
                ),
                **self.serialize_url_param(
                    "clusterPoolName", self.ctx.args.cluster_pool_name,
                    required=True,
                ),
                **self.serialize_url_param(
                    "resourceGroupName", self.ctx.args.resource_group,
                    required=True,
                ),
                **self.serialize_url_param(
                    "subscriptionId", self.ctx.subscription_id,
                    required=True,
                ),
            }
            return parameters

        @property
        def query_parameters(self):
            parameters = {
                **self.serialize_query_param(
                    "api-version", "2024-05-01",
                    required=True,
                ),
            }
            return parameters

        @property
        def header_parameters(self):
            parameters = {
                **self.serialize_header_param(
                    "Accept", "application/json",
                ),
            }
            return parameters

        def on_200(self, session):
            data = self.deserialize_http_content(session)
            self.ctx.set_var(
                "instance",
                data,
                schema_builder=self._build_schema_on_200
            )

        _schema_on_200 = None

        @classmethod
        def _build_schema_on_200(cls):
            if cls._schema_on_200 is not None:
                return cls._schema_on_200

            cls._schema_on_200 = AAZObjectType()

            _schema_on_200 = cls._schema_on_200
            _schema_on_200.next_link = AAZStrType(
                serialized_name="nextLink",
            )
            _schema_on_200.value = AAZListType(
                flags={"required": True},
            )

            value = cls._schema_on_200.value
            value.Element = AAZObjectType()

            _element = cls._schema_on_200.value.Element
            _element.id = AAZStrType(
                flags={"read_only": True},
            )
            _element.name = AAZStrType(
                flags={"read_only": True},
            )
            _element.properties = AAZObjectType(
                flags={"client_flatten": True},
            )
            _element.system_data = AAZObjectType(
                serialized_name="systemData",
                flags={"read_only": True},
            )
            _element.type = AAZStrType(
                flags={"read_only": True},
            )

            properties = cls._schema_on_200.value.Element.properties
            properties.upgrade_type = AAZStrType(
                serialized_name="upgradeType",
                flags={"required": True},
            )

            disc_aks_patch_upgrade = cls._schema_on_200.value.Element.properties.discriminate_by("upgrade_type", "AKSPatchUpgrade")
            disc_aks_patch_upgrade.current_version = AAZStrType(
                serialized_name="currentVersion",
            )
            disc_aks_patch_upgrade.current_version_status = AAZStrType(
                serialized_name="currentVersionStatus",
            )
            disc_aks_patch_upgrade.latest_version = AAZStrType(
                serialized_name="latestVersion",
            )

            disc_cluster_available_in_place_upgrade_properties = cls._schema_on_200.value.Element.properties.discriminate_by("upgrade_type", "ClusterAvailableInPlaceUpgradeProperties")
            disc_cluster_available_in_place_upgrade_properties.component_name = AAZStrType(
                serialized_name="componentName",
            )
            disc_cluster_available_in_place_upgrade_properties.created_time = AAZStrType(
                serialized_name="createdTime",
            )
            disc_cluster_available_in_place_upgrade_properties.description = AAZStrType()
            disc_cluster_available_in_place_upgrade_properties.extended_properties = AAZStrType(
                serialized_name="extendedProperties",
            )
            disc_cluster_available_in_place_upgrade_properties.severity = AAZStrType()
            disc_cluster_available_in_place_upgrade_properties.source_build_number = AAZStrType(
                serialized_name="sourceBuildNumber",
            )
            disc_cluster_available_in_place_upgrade_properties.source_cluster_version = AAZStrType(
                serialized_name="sourceClusterVersion",
            )
            disc_cluster_available_in_place_upgrade_properties.source_oss_version = AAZStrType(
                serialized_name="sourceOssVersion",
            )
            disc_cluster_available_in_place_upgrade_properties.target_build_number = AAZStrType(
                serialized_name="targetBuildNumber",
            )
            disc_cluster_available_in_place_upgrade_properties.target_cluster_version = AAZStrType(
                serialized_name="targetClusterVersion",
            )
            disc_cluster_available_in_place_upgrade_properties.target_oss_version = AAZStrType(
                serialized_name="targetOssVersion",
            )

            disc_hotfix_upgrade = cls._schema_on_200.value.Element.properties.discriminate_by("upgrade_type", "HotfixUpgrade")
            disc_hotfix_upgrade.component_name = AAZStrType(
                serialized_name="componentName",
            )
            disc_hotfix_upgrade.created_time = AAZStrType(
                serialized_name="createdTime",
            )
            disc_hotfix_upgrade.description = AAZStrType()
            disc_hotfix_upgrade.extended_properties = AAZStrType(
                serialized_name="extendedProperties",
            )
            disc_hotfix_upgrade.severity = AAZStrType()
            disc_hotfix_upgrade.source_build_number = AAZStrType(
                serialized_name="sourceBuildNumber",
            )
            disc_hotfix_upgrade.source_cluster_version = AAZStrType(
                serialized_name="sourceClusterVersion",
            )
            disc_hotfix_upgrade.source_oss_version = AAZStrType(
                serialized_name="sourceOssVersion",
            )
            disc_hotfix_upgrade.target_build_number = AAZStrType(
                serialized_name="targetBuildNumber",
            )
            disc_hotfix_upgrade.target_cluster_version = AAZStrType(
                serialized_name="targetClusterVersion",
            )
            disc_hotfix_upgrade.target_oss_version = AAZStrType(
                serialized_name="targetOssVersion",
            )

            disc_patch_version_upgrade = cls._schema_on_200.value.Element.properties.discriminate_by("upgrade_type", "PatchVersionUpgrade")
            disc_patch_version_upgrade.component_name = AAZStrType(
                serialized_name="componentName",
            )
            disc_patch_version_upgrade.created_time = AAZStrType(
                serialized_name="createdTime",
            )
            disc_patch_version_upgrade.description = AAZStrType()
            disc_patch_version_upgrade.extended_properties = AAZStrType(
                serialized_name="extendedProperties",
            )
            disc_patch_version_upgrade.severity = AAZStrType()
            disc_patch_version_upgrade.source_build_number = AAZStrType(
                serialized_name="sourceBuildNumber",
            )
            disc_patch_version_upgrade.source_cluster_version = AAZStrType(
                serialized_name="sourceClusterVersion",
            )
            disc_patch_version_upgrade.source_oss_version = AAZStrType(
                serialized_name="sourceOssVersion",
            )
            disc_patch_version_upgrade.target_build_number = AAZStrType(
                serialized_name="targetBuildNumber",
            )
            disc_patch_version_upgrade.target_cluster_version = AAZStrType(
                serialized_name="targetClusterVersion",
            )
            disc_patch_version_upgrade.target_oss_version = AAZStrType(
                serialized_name="targetOssVersion",
            )

            system_data = cls._schema_on_200.value.Element.system_data
            system_data.created_at = AAZStrType(
                serialized_name="createdAt",
            )
            system_data.created_by = AAZStrType(
                serialized_name="createdBy",
            )
            system_data.created_by_type = AAZStrType(
                serialized_name="createdByType",
            )
            system_data.last_modified_at = AAZStrType(
                serialized_name="lastModifiedAt",
            )
            system_data.last_modified_by = AAZStrType(
                serialized_name="lastModifiedBy",
            )
            system_data.last_modified_by_type = AAZStrType(
                serialized_name="lastModifiedByType",
            )

            return cls._schema_on_200


class _ListHelper:
    """Helper class for List"""


__all__ = ["List"]