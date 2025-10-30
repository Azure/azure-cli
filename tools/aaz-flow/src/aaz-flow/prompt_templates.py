# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

"""Prompt templates and static guidance for AAZ Flow tools."""

IDEAL_STYLE = """
    @ResourceGroupPreparer(name_prefix="cli_test_ag_with_non_v2_sku_", location="westus")
    def test_ag_with_non_v2_sku(self):
        self.kwargs.update({
            "ag_name": self.create_random_name("ag-", 12),
            "port_name": self.create_random_name("port-", 12),
            "lisener_name": self.create_random_name("lisener-", 12),
            "rule_name": self.create_random_name("rule-", 12),
        })

        self.cmd("network application-gateway create -n {ag_name} -g {rg} --sku WAF_Medium")

        self.kwargs["front_ip"] = self.cmd("network application-gateway show -n {ag_name} -g {rg}").get_output_in_json()["frontendIPConfigurations"][0]["name"]
        self.cmd("network application-gateway frontend-port create -n {port_name} -g {rg} --gateway-name {ag_name} --port 8080")
        self.cmd("network application-gateway http-listener create -n {lisener_name} -g {rg} --gateway-name {ag_name} --frontend-ip {front_ip} --frontend-port {port_name}")

        self.cmd(
            "network application-gateway rule create -n {rule_name} -g {rg} --gateway-name {ag_name} --http-listener {lisener_name}",
            checks=[
                self.check("name", "{ag_name}"),
                self.check("sku.tier", "WAF")
            ]
        )

        self.cmd("network application-gateway delete -n {ag_name} -g {rg}")
"""

def get_testgen_static_instructions() -> str:
    return (
        "You are generating Azure CLI scenario tests for a new module.\n"
        "Follow the style used by azure-cli scenario tests. Keep tests idempotent and light.\n"
        "Generate tests that achieve at least 80%% coverage of methods and parameters covering primary commands for the target module.\n"
        "To understand the primary commands that need to be tested, read through and understand the target module's generated AAZ commands.\n"
        "Constraints: \n"
        "- Keep tests safe-by-default; avoid destructive operations unless clearly required.\n"
        "- Ensure tests can run in parallel without conflicts.\n"
        "- If tests are large and can be safely and logically split, create multiple test methods (i.e. avoid a single CRUD test if possible, split it into multiple tests if logically and safely separable).\n"
        "- It is highly preferred that all CRUD operations are not coupled in a single test.\n"
        "- Output only valid Python code for the test file, nothing else."
    )


REF_STYLE_LABEL = "Read and reference the following test files (do not copy verbatim, just follow structure):\n"
