# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
"""Public Active Backup commands layered over the generated web resource commands.

Keep CLI naming and behavior here so regenerating aaz/latest does not discard them.
"""

from azure.cli.core.aaz import AAZCommandGroup, register_command, register_command_group
from knack.help_files import helps

from .aaz.latest.web.serverfarm import silo as plan_silo
from .aaz.latest.web.serverfarm.silo.virtual_network_integration import Show as PlanVnetShow
from .aaz.latest.web.site._refresh_silo import RefreshSilo
from .aaz.latest.web.site import silo as site_silo
from .aaz.latest.web.site.last_known_good import List as LastKnownGoodList
from .aaz.latest.web.site.last_known_good.default import Mark as LastKnownGoodMark, Show as LastKnownGoodShow
from .aaz.latest.web.site.managed_traffic_config import List as ManagedTrafficList
from .aaz.latest.web.site.managed_traffic_config.default import (
    Show as ManagedTrafficShow, Update as ManagedTrafficUpdate,
)
from .aaz.latest.web.site.silo.virtual_network_connection import virtual_network as site_vnet


# pylint: disable=protected-access,too-few-public-methods
class _ActiveBackupArguments:
    # Generated builders cache on cls; isolate these caches from the generated classes.
    _args_schema = None
    _arguments_schema = None

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        schema = super()._build_arguments_schema(*args, **kwargs)
        options = {
            "name": ["-n", "--name"],
            "silo_name": ["--silo"],
            "instance_number_override": ["--number-of-workers"],
            "zone_redundant_override": ["--zone-redundant"],
            "primary_server_farm_name": ["--primary-plan-name", "--primary-server-farm-name"],
            "subnet_resource_id": ["--subnet"],
        }
        for field, aliases in options.items():
            if hasattr(schema, field):
                argument = schema[field]
                argument._options = aliases
                argument._help["name"] = " ".join(aliases)
        if cls.AZ_NAME in ("appservice plan silo create", "webapp silo create"):
            schema.primary_location._required = True
        return schema


@register_command("appservice plan silo create", is_preview=True)
class PlanSiloCreate(_ActiveBackupArguments, plan_silo.Create):
    """Create an App Service plan silo.

    :example: Create a plan silo in a secondary region.
        az appservice plan silo create -g rg -n plan --silo backup --location westus2 --primary-location eastus
    """


@register_command("appservice plan silo update", is_preview=True)
class PlanSiloUpdate(_ActiveBackupArguments, plan_silo.Update):
    """Update an App Service plan silo."""


@register_command("appservice plan silo show", is_preview=True)
class PlanSiloShow(_ActiveBackupArguments, plan_silo.Show):
    """Show an App Service plan silo."""


@register_command("appservice plan silo list", is_preview=True)
class PlanSiloList(_ActiveBackupArguments, plan_silo.List):
    """List the silos of an App Service plan."""


@register_command("appservice plan silo delete", is_preview=True)
class PlanSiloDelete(_ActiveBackupArguments, plan_silo.Delete):
    """Delete an App Service plan silo."""


@register_command("appservice plan silo wait", is_preview=True)
class PlanSiloWait(_ActiveBackupArguments, plan_silo.Wait):
    """Wait for an App Service plan silo to satisfy a condition."""


@register_command("appservice plan silo vnet-integration list", is_preview=True)
class PlanSiloVnetList(_ActiveBackupArguments, PlanVnetShow):
    """Show the virtual network integrations of an App Service plan silo."""

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        schema = super()._build_arguments_schema(*args, **kwargs)
        schema.name._id_part = None
        return schema


@register_command("webapp silo create", is_preview=True)
class WebappSiloCreate(_ActiveBackupArguments, site_silo.Create):
    """Create a web app silo.

    :example: Create a web app silo after creating its backing plan silo.
        az webapp silo create -g rg -n app --silo backup --location westus2 --primary-location eastus
    """


@register_command("webapp silo update", is_preview=True)
class WebappSiloUpdate(_ActiveBackupArguments, site_silo.Update):
    """Update a web app silo."""


@register_command("webapp silo show", is_preview=True)
class WebappSiloShow(_ActiveBackupArguments, site_silo.Show):
    """Show a web app silo."""


@register_command("webapp silo list", is_preview=True)
class WebappSiloList(_ActiveBackupArguments, site_silo.List):
    """List the silos of a web app."""


@register_command("webapp silo delete", is_preview=True)
class WebappSiloDelete(_ActiveBackupArguments, site_silo.Delete):
    """Delete a web app silo."""


@register_command("webapp silo wait", is_preview=True)
class WebappSiloWait(_ActiveBackupArguments, site_silo.Wait):
    """Wait for a web app silo to satisfy a condition."""


@register_command("webapp silo refresh", is_preview=True)
class WebappSiloRefresh(_ActiveBackupArguments, RefreshSilo):
    """Refresh the silos of the primary web app."""


@register_command("webapp silo vnet-integration show", is_preview=True)
class WebappSiloVnetShow(_ActiveBackupArguments, site_vnet.Show):
    """Show the virtual network connection of a web app silo."""


@register_command("webapp silo vnet-integration add", is_preview=True)
class WebappSiloVnetAdd(_ActiveBackupArguments, site_vnet.Create):
    """Add a virtual network connection to a web app silo."""


@register_command("webapp silo vnet-integration remove", is_preview=True)
class WebappSiloVnetRemove(_ActiveBackupArguments, site_vnet.Delete):
    """Remove the virtual network connection of a web app silo."""


@register_command("webapp silo vnet-integration update", is_preview=True)
class WebappSiloVnetUpdate(_ActiveBackupArguments, site_vnet.Update):
    """Update a web app silo's virtual network connection using PATCH."""

    AZ_SUPPORT_GENERIC_UPDATE = False

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        schema = super()._build_arguments_schema(*args, **kwargs)
        for field in ("subnet_resource_id", "swift_supported", "kind"):
            schema[field]._nullable = False
        schema.kind._arg_group = "Properties"
        return schema

    def _execute_operations(self):
        self.pre_operations()
        self.PatchConnection(ctx=self.ctx)()
        self.post_operations()

    class PatchConnection(site_vnet.Create.SiteSiloVirtualNetworkConnectionsCreateOrUpdateSiteSiloVnetConnection):
        @property
        def method(self):
            return "PATCH"

        def __call__(self, *args, **kwargs):
            request = self.make_request()
            session = self.client.send_request(request=request, stream=False, **kwargs)
            if session.http_response.status_code == 200:
                return self.on_200_201(session)
            return self.on_error(session.http_response)


@register_command("webapp managed-traffic list", is_preview=True)
class WebappManagedTrafficList(_ActiveBackupArguments, ManagedTrafficList):
    """List the managed traffic configurations of a web app."""


@register_command("webapp managed-traffic show", is_preview=True)
class WebappManagedTrafficShow(_ActiveBackupArguments, ManagedTrafficShow):
    """Show the default managed traffic configuration of a web app."""


@register_command("webapp managed-traffic update", is_preview=True)
class WebappManagedTrafficUpdate(_ActiveBackupArguments, ManagedTrafficUpdate):
    """Update the default managed traffic configuration of a web app."""


@register_command("webapp last-known-good list", is_preview=True)
class WebappLastKnownGoodList(_ActiveBackupArguments, LastKnownGoodList):
    """List the last known good configurations of a web app."""


@register_command("webapp last-known-good show", is_preview=True)
class WebappLastKnownGoodShow(_ActiveBackupArguments, LastKnownGoodShow):
    """Show the default last known good configuration of a web app."""


@register_command("webapp last-known-good mark", is_preview=True)
class WebappLastKnownGoodMark(_ActiveBackupArguments, LastKnownGoodMark):
    """Mark the latest ready revision of a web app as last known good."""


@register_command_group("appservice plan silo", is_preview=True)
class PlanSiloGroup(AAZCommandGroup):
    """Manage Active Backup silos for an App Service plan."""


@register_command_group("appservice plan silo vnet-integration", is_preview=True)
class PlanSiloVnetGroup(AAZCommandGroup):
    """Inspect an App Service plan silo's virtual network integrations."""


@register_command_group("webapp silo", is_preview=True)
class WebappSiloGroup(AAZCommandGroup):
    """Manage Active Backup silos for a web app."""


@register_command_group("webapp silo vnet-integration", is_preview=True)
class WebappSiloVnetGroup(AAZCommandGroup):
    """Manage a web app silo's virtual network connection."""


@register_command_group("webapp managed-traffic", is_preview=True)
class WebappManagedTrafficGroup(AAZCommandGroup):
    """Manage a web app's Active Backup traffic configuration."""


@register_command_group("webapp last-known-good", is_preview=True)
class WebappLastKnownGoodGroup(AAZCommandGroup):
    """Manage a web app's last known good configuration."""


def load_command_table(loader):
    generated_groups = (
        "web serverfarm silo", "web site silo", "web site managed-traffic-config", "web site last-known-good",
    )
    for table in (loader.command_table, loader.command_group_table, helps):
        for name in list(table):
            if name == "web site refresh-silo" or any(
                    name == group or name.startswith(group + " ") for group in generated_groups):
                del table[name]

    commands = (
        PlanSiloCreate, PlanSiloUpdate, PlanSiloShow, PlanSiloList, PlanSiloDelete, PlanSiloWait, PlanSiloVnetList,
        WebappSiloCreate, WebappSiloUpdate, WebappSiloShow, WebappSiloList, WebappSiloDelete, WebappSiloWait,
        WebappSiloRefresh, WebappSiloVnetShow, WebappSiloVnetAdd, WebappSiloVnetUpdate,
        WebappSiloVnetRemove, WebappManagedTrafficList, WebappManagedTrafficShow, WebappManagedTrafficUpdate,
        WebappLastKnownGoodList, WebappLastKnownGoodShow, WebappLastKnownGoodMark,
    )
    for command in commands:
        loader.command_table[command.AZ_NAME] = command(loader=loader)
    for group in (
            PlanSiloGroup, PlanSiloVnetGroup, WebappSiloGroup, WebappSiloVnetGroup,
            WebappManagedTrafficGroup, WebappLastKnownGoodGroup):
        loader.command_group_table[group.AZ_NAME] = group(cli_ctx=loader.cli_ctx)
