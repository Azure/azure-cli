# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=no-self-use, line-too-long, protected-access, too-few-public-methods, unused-argument
from knack.log import get_logger

from azure.cli.core.aaz import AAZObjectType, AAZBoolType, AAZDictType, AAZFreeFormDictType, AAZStrType, AAZListType, has_value
from ..aaz.latest.vm.extension import Show as _VMExtensionShow, Create as _VMExtensionCreate

logger = get_logger(__name__)


class VMExtensionShow(_VMExtensionShow):

    class VirtualMachineExtensionsGet(_VMExtensionShow.VirtualMachineExtensionsGet):

        # Overrride to solve key conflict of _schema_on_200.properties.type when deserializing output
        # Keep sync other properties with aaz generated code
        @classmethod
        def _build_schema_on_200(cls):
            from ..aaz.latest.vm.extension._show import _ShowHelper

            if cls._schema_on_200 is not None:
                return cls._schema_on_200

            cls._schema_on_200 = AAZObjectType()

            _schema_on_200 = cls._schema_on_200
            _schema_on_200.id = AAZStrType(
                flags={"read_only": True},
            )
            _schema_on_200.location = AAZStrType()
            _schema_on_200.name = AAZStrType(
                flags={"read_only": True},
            )
            _schema_on_200.properties = AAZObjectType(
                flags={"client_flatten": True},
            )
            _schema_on_200.tags = AAZDictType()
            _schema_on_200.type = AAZStrType(
                flags={"read_only": True},
            )

            properties = cls._schema_on_200.properties
            properties.auto_upgrade_minor_version = AAZBoolType(
                serialized_name="autoUpgradeMinorVersion",
            )
            properties.enable_automatic_upgrade = AAZBoolType(
                serialized_name="enableAutomaticUpgrade",
            )
            properties.force_update_tag = AAZStrType(
                serialized_name="forceUpdateTag",
            )
            properties.instance_view = AAZObjectType(
                serialized_name="instanceView",
            )
            properties.protected_settings = AAZFreeFormDictType(
                serialized_name="protectedSettings",
            )
            properties.protected_settings_from_key_vault = AAZObjectType(
                serialized_name="protectedSettingsFromKeyVault",
            )
            properties.provision_after_extensions = AAZListType(
                serialized_name="provisionAfterExtensions",
            )
            properties.provisioning_state = AAZStrType(
                serialized_name="provisioningState",
                flags={"read_only": True},
            )
            properties.publisher = AAZStrType()
            properties.settings = AAZFreeFormDictType()
            properties.suppress_failures = AAZBoolType(
                serialized_name="suppressFailures",
            )
            properties.type = AAZStrType(
                serialized_name="typePropertiesType",
            )
            properties.type_handler_version = AAZStrType(
                serialized_name="typeHandlerVersion",
            )

            instance_view = cls._schema_on_200.properties.instance_view
            instance_view.name = AAZStrType()
            instance_view.statuses = AAZListType()
            instance_view.substatuses = AAZListType()
            instance_view.type = AAZStrType()
            instance_view.type_handler_version = AAZStrType(
                serialized_name="typeHandlerVersion",
            )

            statuses = cls._schema_on_200.properties.instance_view.statuses
            statuses.Element = AAZObjectType()
            _ShowHelper._build_schema_instance_view_status_read(statuses.Element)

            substatuses = cls._schema_on_200.properties.instance_view.substatuses
            substatuses.Element = AAZObjectType()
            _ShowHelper._build_schema_instance_view_status_read(substatuses.Element)

            protected_settings_from_key_vault = cls._schema_on_200.properties.protected_settings_from_key_vault
            protected_settings_from_key_vault.secret_url = AAZStrType(
                serialized_name="secretUrl",
                flags={"required": True},
            )
            protected_settings_from_key_vault.source_vault = AAZObjectType(
                serialized_name="sourceVault",
                flags={"required": True},
            )

            source_vault = cls._schema_on_200.properties.protected_settings_from_key_vault.source_vault
            source_vault.id = AAZStrType()

            provision_after_extensions = cls._schema_on_200.properties.provision_after_extensions
            provision_after_extensions.Element = AAZStrType()

            tags = cls._schema_on_200.tags
            tags.Element = AAZStrType()

            return cls._schema_on_200


class VMExtensionCreate(_VMExtensionCreate):

    class VirtualMachineExtensionsCreateOrUpdate(_VMExtensionCreate.VirtualMachineExtensionsCreateOrUpdate):

        # Overrride to solve key conflict of _schema_on_200.properties.type when deserializing output
        # Keep sync other properties with aaz generated code
        @classmethod
        def _build_schema_on_200_201(cls):
            from ..aaz.latest.vm.extension._create import _CreateHelper

            if cls._schema_on_200_201 is not None:
                return cls._schema_on_200_201

            cls._schema_on_200_201 = AAZObjectType()

            _schema_on_200_201 = cls._schema_on_200_201
            _schema_on_200_201.id = AAZStrType(
                flags={"read_only": True},
            )
            _schema_on_200_201.location = AAZStrType()
            _schema_on_200_201.name = AAZStrType(
                flags={"read_only": True},
            )
            _schema_on_200_201.properties = AAZObjectType(
                flags={"client_flatten": True},
            )
            _schema_on_200_201.tags = AAZDictType()
            _schema_on_200_201.type = AAZStrType(
                flags={"read_only": True},
            )

            properties = cls._schema_on_200_201.properties
            properties.auto_upgrade_minor_version = AAZBoolType(
                serialized_name="autoUpgradeMinorVersion",
            )
            properties.enable_automatic_upgrade = AAZBoolType(
                serialized_name="enableAutomaticUpgrade",
            )
            properties.force_update_tag = AAZStrType(
                serialized_name="forceUpdateTag",
            )
            properties.instance_view = AAZObjectType(
                serialized_name="instanceView",
            )
            properties.protected_settings = AAZFreeFormDictType(
                serialized_name="protectedSettings",
            )
            properties.protected_settings_from_key_vault = AAZObjectType(
                serialized_name="protectedSettingsFromKeyVault",
            )
            properties.provision_after_extensions = AAZListType(
                serialized_name="provisionAfterExtensions",
            )
            properties.provisioning_state = AAZStrType(
                serialized_name="provisioningState",
                flags={"read_only": True},
            )
            properties.publisher = AAZStrType()
            properties.settings = AAZFreeFormDictType()
            properties.suppress_failures = AAZBoolType(
                serialized_name="suppressFailures",
            )
            properties.type = AAZStrType(
                serialized_name="typePropertiesType"
            )
            properties.type_handler_version = AAZStrType(
                serialized_name="typeHandlerVersion",
            )

            instance_view = cls._schema_on_200_201.properties.instance_view
            instance_view.name = AAZStrType()
            instance_view.statuses = AAZListType()
            instance_view.substatuses = AAZListType()
            instance_view.type = AAZStrType()
            instance_view.type_handler_version = AAZStrType(
                serialized_name="typeHandlerVersion",
            )

            statuses = cls._schema_on_200_201.properties.instance_view.statuses
            statuses.Element = AAZObjectType()
            _CreateHelper._build_schema_instance_view_status_read(statuses.Element)

            substatuses = cls._schema_on_200_201.properties.instance_view.substatuses
            substatuses.Element = AAZObjectType()
            _CreateHelper._build_schema_instance_view_status_read(substatuses.Element)

            protected_settings_from_key_vault = cls._schema_on_200_201.properties.protected_settings_from_key_vault
            protected_settings_from_key_vault.secret_url = AAZStrType(
                serialized_name="secretUrl",
                flags={"required": True},
            )
            protected_settings_from_key_vault.source_vault = AAZObjectType(
                serialized_name="sourceVault",
                flags={"required": True},
            )

            source_vault = cls._schema_on_200_201.properties.protected_settings_from_key_vault.source_vault
            source_vault.id = AAZStrType()

            provision_after_extensions = cls._schema_on_200_201.properties.provision_after_extensions
            provision_after_extensions.Element = AAZStrType()

            tags = cls._schema_on_200_201.tags
            tags.Element = AAZStrType()

            return cls._schema_on_200_201
