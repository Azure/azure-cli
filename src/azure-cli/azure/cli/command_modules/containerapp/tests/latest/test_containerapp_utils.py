# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
import unittest
import os

from azure.cli.command_modules.containerapp._utils import clean_null_values, load_cert_file
TEST_DIR = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))


class UtilsTest(unittest.TestCase):
    def test_clean_empty_values(self):
        test_dict = {

        }
        result = clean_null_values(test_dict)
        self.assertEqual({}, result)

        test_dict["properties"] = {}

        result_new = clean_null_values(test_dict)
        result_old = old_clean_null_values(test_dict)

        #  test remove empty {}
        expect_result = {}
        self.assertEqual(expect_result, result_new)
        self.assertEqual(result_new, result_old)

        test_dict = {
            "properties": {
                "environmentId": None,
                "test": {},
                "configuration": {
                    "secrets": None,
                    "activeRevisionsMode": None,
                    "ingress": {
                        "fqdn": None,
                        "external": None,
                        "targetPort": None,
                        "exposedPort": None,
                        "transport": None,
                        "traffic": [
                            {
                                "revisionName": None,
                                "weight": None,
                                "latestRevision": None,
                                "label": None
                            }
                        ],
                        "customDomains": None,
                        "allowInsecure": None,
                        "ipSecurityRestrictions": None,
                        "stickySessions": None,
                        "clientCertificateMode": None,
                        "corsPolicy": None
                    },
                    "registries": None,
                    "dapr": None,
                    "maxInactiveRevisions": None
                },
            },
        }

        #  test remove empty {}
        result_new = clean_null_values(test_dict)
        result_old = old_clean_null_values(test_dict)

        expect_result = {'properties': {'configuration': {'ingress': {'traffic': []}}}}
        self.assertEqual(expect_result, result_new)
        self.assertEqual(result_new, result_old)

        test_dict = {
            "properties": {
                "environmentId": None,
                "test": {},
                "configuration": {
                    "secrets": None,
                    "activeRevisionsMode": "Single",
                    "ingress": {
                        "fqdn": None,
                        "external": None,
                        "targetPort": 80,
                        "exposedPort": None,
                        "transport": "Auto",
                        "traffic": [
                            {
                                "revisionName": None,
                                "weight": 100,
                                "latestRevision": None,
                                "label": None
                            }
                        ],
                        "customDomains": None,
                        "allowInsecure": None,
                        "ipSecurityRestrictions": None,
                        "stickySessions": None,
                        "clientCertificateMode": None,
                        "corsPolicy": None
                    },
                    "registries": None,
                    "dapr": None,
                    "maxInactiveRevisions": None
                },
            },
        }

        result_new = clean_null_values(test_dict)
        result_old = old_clean_null_values(test_dict)

        expect_result = {
            'properties': {
                'configuration': {
                    'activeRevisionsMode': 'Single',
                    'ingress': {
                        'targetPort': 80,
                        'traffic': [
                            {
                                'weight': 100
                            }
                        ],
                        'transport': 'Auto'
                    }
                }
            }
        }
        self.assertEqual(expect_result, result_new)
        self.assertEqual(result_new, result_old)

        test_dict = {
            "properties": {
                "environmentId": None,
                "test": {
                    "secrets": "secretTest",
                },
                "configuration": {
                    "secrets": None,
                    "activeRevisionsMode": "Single",
                    "ingress": {
                        "fqdn": None,
                        "external": None,
                        "targetPort": 80,
                        "exposedPort": None,
                        "transport": "Auto",
                        "traffic": [
                            {
                                "revisionName": None,
                                "weight": 100,
                                "latestRevision": 0,
                                "label": None
                            }
                        ],
                        "customDomains": None,
                        "allowInsecure": 0,
                        "ipSecurityRestrictions": None,
                        "stickySessions": None,
                        "clientCertificateMode": None,
                        "corsPolicy": None
                    },
                    "registries": None,
                    "dapr": None,
                    "maxInactiveRevisions": None
                },
            },
        }

        result_new = clean_null_values(test_dict)
        result_old = old_clean_null_values(test_dict)
        expect_result_for_new = {
            'properties': {
                "test": {
                    "secrets": "secretTest",
                },
                'configuration': {
                    'activeRevisionsMode': 'Single',
                    'ingress': {
                        'targetPort': 80,
                        'traffic': [
                            {
                                'weight': 100,
                                'latestRevision': 0,
                            }
                        ],
                        'allowInsecure': 0,
                        'transport': 'Auto'
                    }
                }
            }
        }
        expect_result_for_old = {
            'properties': {
                "test": {
                    "secrets": "secretTest",
                },
                'configuration': {
                    'activeRevisionsMode': 'Single',
                    'ingress': {
                        'targetPort': 80,
                        'traffic': [
                            {
                                'weight': 100,
                            }
                        ],
                        'transport': 'Auto'
                    }
                }
            }
        }
        self.assertEqual(expect_result_for_new, result_new)
        self.assertEqual(expect_result_for_old, result_old)

    def test_load_cert_file(self):
        pfx_file = os.path.join(TEST_DIR, 'data', 'cert.pfx')
        testpassword = 'test12'
        blob, thumbprint = load_cert_file(pfx_file, testpassword)
        self.assertEqual("8D2DC3BF7DF8D2BA32705E079A9C0015FE9CBC7062C8583FE19B7F068AFDC2C9", thumbprint)

        pem_file = os.path.join(TEST_DIR, 'data', 'cert.pem')
        blob, thumbprint = load_cert_file(pem_file)
        self.assertEqual("FEAD2E32FB423702763C1093ACD431E2A05CD55F1419F4BAA6CD5E64030EF499", thumbprint)


# Remove null/None/empty properties in a model since the PATCH API will delete those. Not needed once we move to the SDK
# This old version will remove properties which value is 0
# The new version is to fix this bug and should not change other behaviors
def old_clean_null_values(d):
    if isinstance(d, dict):
        return {
            k: v
            for k, v in ((k, old_clean_null_values(v)) for k, v in d.items())
            if v or isinstance(v, list)
        }
    if isinstance(d, list):
        return [v for v in map(old_clean_null_values, d) if v]
    return d
