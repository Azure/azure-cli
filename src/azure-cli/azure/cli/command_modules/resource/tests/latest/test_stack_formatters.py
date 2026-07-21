# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import json
import os
import unittest

import azure.mgmt.resource.deploymentstacks.models as StackModels

from azure.cli.command_modules.resource._color import Color
from azure.cli.command_modules.resource._stacks_formatters import DeploymentStacksWhatIfResultFormatter


class TestStacksWhatIfResultFormatter(unittest.TestCase):

    def test_what_if_1(self):
        what_if_result = self._get_stacks_what_if_result("what-if-1.json")

        formatted = DeploymentStacksWhatIfResultFormatter().format(what_if_result)
        self.assertEqual(self.EXPECTED_STACKS_WHAT_IF_1, formatted)

        expected_no_color_result = self.EXPECTED_STACKS_WHAT_IF_1
        for color in list(Color):
            expected_no_color_result = expected_no_color_result.replace(str(color), '')

        self.assertEqual(
            expected_no_color_result, DeploymentStacksWhatIfResultFormatter(enable_color=False).format(what_if_result))
        
    def test_what_if_2(self):
        what_if_result = self._get_stacks_what_if_result("what-if-2.json")

        formatted = DeploymentStacksWhatIfResultFormatter().format(what_if_result)
        self.assertEqual(self.EXPECTED_STACKS_WHAT_IF_2, formatted)

        expected_no_color_result = self.EXPECTED_STACKS_WHAT_IF_2
        for color in list(Color):
            expected_no_color_result = expected_no_color_result.replace(str(color), '')

        self.assertEqual(
            expected_no_color_result, DeploymentStacksWhatIfResultFormatter(enable_color=False).format(what_if_result))

    def _get_stacks_what_if_result(self, file_name: str):
        return StackModels.DeploymentStacksWhatIfResult(self._get_stacks_what_if_json(file_name))

    @staticmethod
    def _get_stacks_what_if_json(file_name: str):
        with open(TestStacksWhatIfResultFormatter._get_stacks_what_if_test_file_path(file_name), 'r') as f:
            return json.load(f)

    @staticmethod
    def _get_stacks_what_if_test_file_path(file_name: str):
        curr_dir = os.path.dirname(os.path.realpath(__file__))
        return os.path.join(curr_dir, 'data', 'stacks-what-if', file_name)

    EXPECTED_STACKS_WHAT_IF_1 = f"""Resource and property changes are indicated with these symbols:
  {Color.GREEN}+{Color.RESET} Create              ! Unsupported
  {Color.PURPLE}~{Color.RESET} Modify              {Color.RED}-{Color.RESET} Delete
  = NoChange            {Color.BLUE}v{Color.RESET} Detach

{Color.DARK_YELLOW}Changes to Stack /subscriptions/6d41d86d-eb6b-473a-b31d-bbd084e1814d/resourceGroups/503ace4c-9b1c-4059-a3e9-09553d24e9e1/providers/Microsoft.Resources/deploymentStacks/testStack_9ef16884f0dad7d0e5de3d3ec57:{Color.RESET}
{Color.PURPLE}~ {Color.RESET}DeploymentScope: {Color.PURPLE}"ThisIsBefore"{Color.RESET} => {Color.PURPLE}"ThisIsAfter"{Color.RESET}
{Color.PURPLE}~ {Color.RESET}DenySettings.Mode: {Color.PURPLE}"None"{Color.RESET} => {Color.PURPLE}"DenyDelete"{Color.RESET}
{Color.PURPLE}~ {Color.RESET}DenySettings.ApplyToChildScopes: {Color.PURPLE}"False"{Color.RESET} => {Color.PURPLE}"True"{Color.RESET}
{Color.PURPLE}~ DenySettings.ExcludedPrincipals: {Color.RESET}
  {Color.GREEN}+ {Color.RESET}{Color.GREEN}"004afc20-146e-4932-a8b5-3098461c46a5"{Color.RESET}
  {Color.GREEN}+ {Color.RESET}{Color.GREEN}"e6a513a0-b872-4355-82b9-47645fb30d3a"{Color.RESET}
{Color.PURPLE}~ DenySettings.ArrayOfMixed: {Color.RESET}
  {Color.PURPLE}~{Color.RESET} 0:
    {Color.PURPLE}~ {Color.RESET}properties.something: {Color.PURPLE}"B4"{Color.RESET} => {Color.PURPLE}"Now"{Color.RESET}
  {Color.GREEN}+{Color.RESET} 1:
    {Color.GREEN}+ {Color.RESET}{Color.GREEN}"now"{Color.RESET}
  {Color.RED}-{Color.RESET} 2:
    {Color.RED}- {Color.RESET}{Color.RED}"iWasDeleted"{Color.RESET}

{Color.DARK_YELLOW}Changes to Managed Resources:{Color.RESET}

Azure
  {Color.PURPLE}~ {Color.RESET}{Color.PURPLE}/subscriptions/6d41d86d-eb6b-473a-b31d-bbd084e1814d/resourceGroups/503ace4c-9b1c-4059-a3e9-09553d24e9e1/providers/Microsoft.Test/testA/resourceA [2021-05-01]{Color.RESET}
    = Management Status: "Managed"
    {Color.PURPLE}~ {Color.RESET}Deny Status: {Color.PURPLE}"None"{Color.RESET} => {Color.PURPLE}"DenyDelete"{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}properties.properties1: {Color.PURPLE}"resourceA-before"{Color.RESET} => {Color.PURPLE}"resourceA-after"{Color.RESET}
  = /subscriptions/6d41d86d-eb6b-473a-b31d-bbd084e1814d/resourceGroups/503ace4c-9b1c-4059-a3e9-09553d24e9e1/providers/Microsoft.Test/testB/resourceB [2021-05-01]
    = Management Status: "Managed"
    {Color.PURPLE}~ {Color.RESET}Deny Status: {Color.PURPLE}"None"{Color.RESET} => {Color.PURPLE}"DenyDelete"{Color.RESET}
  {Color.GREEN}+ {Color.RESET}{Color.GREEN}/subscriptions/6d41d86d-eb6b-473a-b31d-bbd084e1814d/resourceGroups/503ace4c-9b1c-4059-a3e9-09553d24e9e1/providers/Microsoft.Test/testD/resourceD [2021-05-01]{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Management Status: {Color.PURPLE}"NotManaged"{Color.RESET} => {Color.PURPLE}"Managed"{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Deny Status: {Color.PURPLE}"None"{Color.RESET} => {Color.PURPLE}"DenyDelete"{Color.RESET}

>> {Color.PURPLE}Potential Resource Changes (Learn more at https://aka.ms/whatIfPotentialChanges){Color.RESET}
  {Color.CYAN}?{Color.RESET}{Color.PURPLE}~ {Color.RESET}{Color.CYAN}[Potential] {Color.RESET}{Color.PURPLE}/subscriptions/6d41d86d-eb6b-473a-b31d-bbd084e1814d/resourceGroups/503ace4c-9b1c-4059-a3e9-09553d24e9e1/providers/Microsoft.Test/testC/resourceC [2021-05-01]{Color.RESET}
    = Management Status: "Managed"
    {Color.PURPLE}~ {Color.RESET}Deny Status: {Color.PURPLE}"None"{Color.RESET} => {Color.PURPLE}"DenyDelete"{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}properties.properties1: {Color.PURPLE}"resourceC-before"{Color.RESET} => {Color.PURPLE}"resourceC-potential-after"{Color.RESET}
  {Color.CYAN}?{Color.RESET}{Color.RED}- {Color.RESET}{Color.CYAN}[Potential] {Color.RESET}{Color.RED}/subscriptions/6d41d86d-eb6b-473a-b31d-bbd084e1814d/resourceGroups/503ace4c-9b1c-4059-a3e9-09553d24e9e1/providers/Microsoft.Test/testC/resourceC{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Management Status: {Color.PURPLE}"Managed"{Color.RESET} => {Color.PURPLE}"NotManaged"{Color.RESET}
    = Deny Status: "None"

Contoso@2.0.0
  {Color.PURPLE}~ {Color.RESET}{Color.PURPLE}Contoso/example name="abcResource" [v1]{Color.RESET}
    = Management Status: "Managed"
    = Deny Status: "NotSupported"
    {Color.PURPLE}~ {Color.RESET}properties.properties1: {Color.PURPLE}"resourceA-before"{Color.RESET} => {Color.PURPLE}"resourceA-after"{Color.RESET}
    {Color.GREEN}+{Color.RESET} properties.someConfig: {Color.GREEN}{{
        "type": "object",
        "value": {{
          "enabled": true,
          "values": [
            1,
            2,
            3
          ]
        }}
      }}{Color.RESET}
    {Color.RED}-{Color.RESET} properties.some.deeply.nested.array: {Color.RED}[
        "one",
        "two"
      ]{Color.RESET}
  {Color.RED}- {Color.RESET}{Color.RED}Contoso/example name="defResource"{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Management Status: {Color.PURPLE}"Managed"{Color.RESET} => {Color.PURPLE}"Unmanaged"{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Deny Status: {Color.PURPLE}"NotSupported"{Color.RESET} => {Color.PURPLE}"None"{Color.RESET}

>> {Color.PURPLE}Potential Resource Changes (Learn more at https://aka.ms/whatIfPotentialChanges){Color.RESET}
  {Color.CYAN}?{Color.RESET}! {Color.CYAN}[Potential] {Color.RESET}Contoso/noPreview 
    {Color.PURPLE}~ {Color.RESET}Management Status: {Color.PURPLE}null{Color.RESET} => {Color.PURPLE}"Managed"{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Deny Status: {Color.PURPLE}null{Color.RESET} => {Color.PURPLE}"NotSupported"{Color.RESET}

Kubernetes@2.0.0 namespace="myNs", kubeconfig=<Secret 'mySecret' in key vault '/subscriptions/00000000-0000-0000-0000-000000000000/resourceGroups/myResourceGroup/providers/Microsoft.KeyVault/vaults/myKeyVault'>
  {Color.GREEN}+ {Color.RESET}{Color.GREEN}app/Deployment name="kubeAppDeployment" [v1]{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Management Status: {Color.PURPLE}null{Color.RESET} => {Color.PURPLE}"Managed"{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Deny Status: {Color.PURPLE}null{Color.RESET} => {Color.PURPLE}"NotApplicable"{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}properties.property1: {Color.PURPLE}"kubeAppDeployment-before"{Color.RESET} => {Color.PURPLE}"kubeAppDeployment-after"{Color.RESET}

{Color.RED}Deleting - {Color.RESET}Resources Marked for Deletion 2 total:

Azure

>> {Color.RED}Potential Deletions 1 total (Learn more at https://aka.ms/whatIfPotentialChanges){Color.RESET}
  {Color.CYAN}?{Color.RESET}{Color.RED}- {Color.RESET}{Color.CYAN}[Potential] {Color.RESET}{Color.RED}/subscriptions/6d41d86d-eb6b-473a-b31d-bbd084e1814d/resourceGroups/503ace4c-9b1c-4059-a3e9-09553d24e9e1/providers/Microsoft.Test/testC/resourceC{Color.RESET}

Contoso@2.0.0
  {Color.RED}- {Color.RESET}{Color.RED}Contoso/example name="defResource"{Color.RESET}

Diagnostics (5):

INFO: [InfoCode]
  Message: InfoMessage

{Color.DARK_YELLOW}WARNING: [Abc]{Color.RESET}
  {Color.DARK_YELLOW}Message: Xyz{Color.RESET}

{Color.DARK_YELLOW}WARNING: [NoSupportForExtensibleResources]{Color.RESET}
  {Color.DARK_YELLOW}Message: Extensible resources are currently not supported{Color.RESET}

{Color.RED}ERROR: [ErrorCode]{Color.RESET}
  {Color.RED}Message: ErrorMessage{Color.RESET}

{Color.RED}ERROR: [ErrorCode]{Color.RESET}
  {Color.RED}Message: This is an error diagnostic with a target.{Color.RESET}
  {Color.RED}Target: /subscriptions/d41d86d-eb6b-473a-b31d-bbd084e1814d/resourceGroups/503ace4c-9b1c-4059-a3e9-09553d24e9e1/providers/Microsoft.Test/tests/testResource{Color.RESET}

"""
    
    EXPECTED_STACKS_WHAT_IF_2 = f"""Resource and property changes are indicated with these symbols:
  {Color.GREEN}+{Color.RESET} Create              ! Unsupported
  {Color.PURPLE}~{Color.RESET} Modify              {Color.RED}-{Color.RESET} Delete
  = NoChange            {Color.BLUE}v{Color.RESET} Detach

{Color.DARK_YELLOW}Changes to Managed Resources:{Color.RESET}

Azure
  {Color.BLUE}v {Color.RESET}{Color.BLUE}/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/Microsoft.Network/networkSecurityGroups/wv-nsg-mjwo5pow6lmvm{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Management Status: {Color.PURPLE}"managed"{Color.RESET} => {Color.PURPLE}"notManaged"{Color.RESET}
    = Deny Status: "none"
  {Color.BLUE}v {Color.RESET}{Color.BLUE}/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/Microsoft.Network/routeTables/wv-routes-mjwo5pow6lmvm{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Management Status: {Color.PURPLE}"managed"{Color.RESET} => {Color.PURPLE}"notManaged"{Color.RESET}
    = Deny Status: "none"
  {Color.BLUE}v {Color.RESET}{Color.BLUE}/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/Microsoft.Network/virtualNetworks/wv-vnet-mjwo5pow6lmvm{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Management Status: {Color.PURPLE}"managed"{Color.RESET} => {Color.PURPLE}"notManaged"{Color.RESET}
    = Deny Status: "none"
  {Color.PURPLE}~ {Color.RESET}{Color.PURPLE}/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/Microsoft.Resources/templateSpecs/wv-spec-mjwo5pow6lmvm [2022-02-01]{Color.RESET}
    = Management Status: "managed"
    = Deny Status: "none"
    {Color.PURPLE}~ {Color.RESET}properties.description: {Color.PURPLE}"Baseline description"{Color.RESET} => {Color.PURPLE}"Updated description with nested content changes"{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}properties.displayName: {Color.PURPLE}"WhatIf visual validation"{Color.RESET} => {Color.PURPLE}"WhatIf visual validation updated"{Color.RESET}
  {Color.PURPLE}~ {Color.RESET}{Color.PURPLE}/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/Microsoft.Resources/templateSpecs/wv-spec-mjwo5pow6lmvm/versions/v1 [2022-02-01]{Color.RESET}
    = Management Status: "managed"
    = Deny Status: "none"
    {Color.PURPLE}~ {Color.RESET}properties.mainTemplate.contentVersion: {Color.PURPLE}"1.0.0.0"{Color.RESET} => {Color.PURPLE}"2.0.0.0"{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}properties.mainTemplate.outputs.state.value: {Color.PURPLE}"before"{Color.RESET} => {Color.PURPLE}"after"{Color.RESET}
    {Color.GREEN}+{Color.RESET} properties.mainTemplate.outputs.nested: {Color.GREEN}{{
        "type": "object",
        "value": {{
          "enabled": true,
          "values": [
            1,
            2,
            3
          ]
        }}
      }}{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}properties.mainTemplate.variables.nestedObject.level1.level2: {Color.PURPLE}"before"{Color.RESET} => {Color.PURPLE}"after"{Color.RESET}
    {Color.GREEN}+{Color.RESET} properties.mainTemplate.variables.nestedObject.level1.addedArray: {Color.GREEN}[
        "one",
        "two"
      ]{Color.RESET}
    {Color.GREEN}+ {Color.RESET}properties.mainTemplate.variables.nestedObject.level1.addedBoolean: {Color.GREEN}True{Color.RESET}
    {Color.GREEN}+{Color.RESET} properties.mainTemplate.parameters: {Color.GREEN}{{
        "message": {{
          "defaultValue": "hello",
          "type": "string"
        }}
      }}{Color.RESET}
  {Color.GREEN}+ {Color.RESET}{Color.GREEN}/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/Microsoft.Storage/storageAccounts/wvcreatemjwo5pow6lmvm [2023-05-01]{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Management Status: {Color.PURPLE}"notManaged"{Color.RESET} => {Color.PURPLE}"managed"{Color.RESET}
    = Deny Status: "none"
  {Color.PURPLE}~ {Color.RESET}{Color.PURPLE}/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/Microsoft.Storage/storageAccounts/wvmodmjwo5pow6lmvm [2023-05-01]{Color.RESET}
    = Management Status: "managed"
    = Deny Status: "none"
    {Color.PURPLE}~ {Color.RESET}sku.name: {Color.PURPLE}"Standard_LRS"{Color.RESET} => {Color.PURPLE}"Standard_GRS"{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}tags.modifiedTag: {Color.PURPLE}"before"{Color.RESET} => {Color.PURPLE}"after"{Color.RESET}
    {Color.RED}- {Color.RESET}tags.oldTag: {Color.RED}"deleted-in-updated-template"{Color.RESET}
    {Color.GREEN}+ {Color.RESET}tags.newTag: {Color.GREEN}"created-in-updated-template"{Color.RESET}
  {Color.BLUE}v {Color.RESET}{Color.BLUE}/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/Microsoft.Storage/storageAccounts/wvremovemjwo5pow6lmvm{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Management Status: {Color.PURPLE}"managed"{Color.RESET} => {Color.PURPLE}"notManaged"{Color.RESET}
    = Deny Status: "none"
  = /subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/Microsoft.Storage/storageAccounts/wvsamemjwo5pow6lmvm [2023-05-01]
    = Management Status: "managed"
    = Deny Status: "none"
  {Color.GREEN}+ {Color.RESET}{Color.GREEN}/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/RP.Namespace/widgets/bar [1999-12-31]{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Management Status: {Color.PURPLE}"notManaged"{Color.RESET} => {Color.PURPLE}"managed"{Color.RESET}
    = Deny Status: "none"
  {Color.GREEN}+ {Color.RESET}{Color.GREEN}/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/RP.Namespace/widgets/foo [1999-12-31]{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Management Status: {Color.PURPLE}"notManaged"{Color.RESET} => {Color.PURPLE}"managed"{Color.RESET}
    = Deny Status: "none"

>> {Color.PURPLE}Potential Resource Changes (Learn more at https://aka.ms/whatIfPotentialChanges){Color.RESET}
  {Color.CYAN}?{Color.RESET}{Color.GREEN}+ {Color.RESET}{Color.CYAN}[Potential] {Color.RESET}{Color.GREEN}/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/Microsoft.Storage/storageAccounts/wvpotcreatemjwo5pow6lmvm [2023-05-01]{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Management Status: {Color.PURPLE}"notManaged"{Color.RESET} => {Color.PURPLE}"managed"{Color.RESET}
    = Deny Status: "none"
  {Color.CYAN}?{Color.RESET}{Color.PURPLE}~ {Color.RESET}{Color.CYAN}[Potential] {Color.RESET}{Color.PURPLE}/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/Microsoft.Storage/storageAccounts/wvpotremovemjwo5pow6lmvm [2023-05-01]{Color.RESET}
    = Management Status: "managed"
    = Deny Status: "none"
    {Color.GREEN}+ {Color.RESET}condition: {Color.GREEN}"[greater(int(utcNow('%f')), 4)]"{Color.RESET}
  {Color.CYAN}?{Color.RESET}{Color.BLUE}v {Color.RESET}{Color.CYAN}[Potential] {Color.RESET}{Color.BLUE}/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/Microsoft.Storage/storageAccounts/wvpotremovemjwo5pow6lmvm{Color.RESET}
    {Color.PURPLE}~ {Color.RESET}Management Status: {Color.PURPLE}"managed"{Color.RESET} => {Color.PURPLE}"notManaged"{Color.RESET}
    = Deny Status: "none"

Diagnostics (2):

{Color.DARK_YELLOW}WARNING: [ResourceDeployedMultipleTimes]{Color.RESET}
  {Color.DARK_YELLOW}Message: The resource '/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/RP.Namespace/widgets/bar' is defined multiple times in this deployment. Only the final state of the resource is shown.{Color.RESET}
  {Color.DARK_YELLOW}Target: /subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/RP.Namespace/widgets/bar{Color.RESET}

{Color.DARK_YELLOW}WARNING: [ResourceDeployedMultipleTimes]{Color.RESET}
  {Color.DARK_YELLOW}Message: The resource '/subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/RP.Namespace/widgets/foo' is defined multiple times in this deployment. Only the final state of the resource is shown.{Color.RESET}
  {Color.DARK_YELLOW}Target: /subscriptions/390ba170-3e2a-41c4-b372-15d9c5ae6e81/resourceGroups/whatif-change-40011/providers/RP.Namespace/widgets/foo{Color.RESET}

"""
