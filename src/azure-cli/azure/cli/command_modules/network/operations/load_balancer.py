from azure.cli.core.aaz import register_command

from ..aaz.latest.network.lb import Delete as _LBDelete, Update as _LBUpdate, List as _LBList, Show as _LBShow


@register_command("network cross-region-lb show")
class CrossRegionLoadBalancerShow(_LBShow):
    """Get the details of a load balancer.

    :example: Get the details of a load balancer.
        az network cross-region-lb show -g MyResourceGroup -n MyLb
    """

@register_command("network cross-region-lb delete")
class CrossRegionLoadBalancerDelete(_LBDelete):
    """Delete the specified load balancer.

    :example: Delete a load balancer.
        az network cross-region-lb delete -g MyResourceGroup -n MyLb
    """

@register_command("network cross-region-lb list")
class CrossRegionLoadBalancerList(_LBList):
    """List load balancers.

    :example: List load balancers.
        az network cross-region-lb list -g MyResourceGroup
    """

@register_command("network cross-region-lb update")
class CrossRegionLoadBalancerUpdate(_LBUpdate):
    """Update a load balancer.

    This command can only be used to update the tags for a load balancer. Name and resource group are immutable and cannot be updated.

    :example: Update the tags of a load balancer.
        az network cross-region-lb update -g MyResourceGroup -n MyLB --tags CostCenter=MyTestGroup
    """
