# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


from azure.cli.testsdk import (ScenarioTest)
from ..._validators import validate_revision_suffix, ValidationError

class ContainerappRevisionSuffixTests(ScenarioTest):
    def test_containerapp_revision_suffix_validation(self):
        #valid suffixes
        validate_revision_suffix("0123-abcd")
        validate_revision_suffix("abcd-0123")
        validate_revision_suffix("abcd")
        validate_revision_suffix("3210")

        #invalid suffixes
        with self.assertRaises(ValidationError):    
            validate_revision_suffix("-0123-abcd")

        with self.assertRaises(ValidationError):
            validate_revision_suffix("0123-abcd-")

        with self.assertRaises(ValidationError):
            validate_revision_suffix("0123--abcd")

        with self.assertRaises(ValidationError):
            validate_revision_suffix("0123-ABcd")
