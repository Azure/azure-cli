# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------
from typing import List


def parseResourceProviderResponseForLocations(resourceProviderResponse):
    supportedLocationMap = {}
    if not resourceProviderResponse.get('resourceTypes'):
        return supportedLocationMap
    resourceTypesRawArr = resourceProviderResponse['resourceTypes']
    for resourceTypeResponse in resourceTypesRawArr:
        if resourceTypeResponse['resourceType'] == 'accounts':
            supportedLocationMap = parseLocations(resourceTypeResponse['locations'])
    return supportedLocationMap


def parseLocations(locations: List[str]) -> List[str]:
    if not locations or len(locations) == 0:
        return []
    return [reduceLocation(location) for location in locations]


def reduceLocation(location: str) -> str:
    if not location:
        return location
    location = location.replace(' ', '').lower()
    return location
