# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
# pylint: disable=line-too-long, protected-access, too-few-public-methods

from ..aaz.latest.policy_insights.attestation import List as AttestationList
from azure.cli.core.aaz import has_value, register_command


@register_command(
    "policy attestation list",
)
class List(AttestationList):
    """List all attestations for a resource.

    :example: List all policy attestations at subscription scope
        az policy attestation list

    :example: List the top two policy attestations at resource group scope
        az policy attestation list -g myRg --top 2

    :example: List all attestations that has the policy assignment id of myPolicyAssignment
        az policy attestation list --filter "PolicyAssignmentId eq '/subscriptions/35ee058e-5fa0-414c-8145-3ebb8d09b6e2/providers/microsoft.authorization/policyassignments/b101830944f246d8a14088c5'"
    """

    def _execute_operations(self):
        self.pre_operations()
        condition_0 = has_value(self.ctx.args.resource_id)
        condition_1 = has_value(self.ctx.args.resource_group) and has_value(
            self.ctx.subscription_id)

        if condition_0:
            self.AttestationsListForResource(ctx=self.ctx)()
        elif condition_1:
            self.AttestationsListForResourceGroup(ctx=self.ctx)()
        else:
            self.AttestationsListForSubscription(ctx=self.ctx)()
        self.post_operations()

    @classmethod
    def _build_arguments_schema(cls, *args, **kwargs):
        args_schema = super()._build_arguments_schema(*args, **kwargs)
        args_schema.resource_id._options.append("--resource")
        return args_schema
