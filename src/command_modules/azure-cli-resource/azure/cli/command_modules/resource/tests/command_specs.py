TEST_SPECS = [
    {
        'test_name': 'resource_group_list',
        'command': 'resource group list --output json',
        'expected_result': """[
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup1131",
    "location": "westus",
    "name": "armclistorageGroup1131",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup1215",
    "location": "westus",
    "name": "armclistorageGroup1215",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup1397",
    "location": "westus",
    "name": "armclistorageGroup1397",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup1530",
    "location": "westus",
    "name": "armclistorageGroup1530",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup1691",
    "location": "westus",
    "name": "armclistorageGroup1691",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup1804",
    "location": "westus",
    "name": "armclistorageGroup1804",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup1982",
    "location": "westus",
    "name": "armclistorageGroup1982",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup2315",
    "location": "westus",
    "name": "armclistorageGroup2315",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup2316",
    "location": "westus",
    "name": "armclistorageGroup2316",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup2732",
    "location": "westus",
    "name": "armclistorageGroup2732",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup3187",
    "location": "westus",
    "name": "armclistorageGroup3187",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup32",
    "location": "westus",
    "name": "armclistorageGroup32",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup3313",
    "location": "westus",
    "name": "armclistorageGroup3313",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup3661",
    "location": "westus",
    "name": "armclistorageGroup3661",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup381",
    "location": "westus",
    "name": "armclistorageGroup381",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup4175",
    "location": "westus",
    "name": "armclistorageGroup4175",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup4834",
    "location": "westus",
    "name": "armclistorageGroup4834",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup4978",
    "location": "westus",
    "name": "armclistorageGroup4978",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup5458",
    "location": "westus",
    "name": "armclistorageGroup5458",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup5584",
    "location": "westus",
    "name": "armclistorageGroup5584",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup5637",
    "location": "westus",
    "name": "armclistorageGroup5637",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup5835",
    "location": "westus",
    "name": "armclistorageGroup5835",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup6020",
    "location": "westus",
    "name": "armclistorageGroup6020",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup7062",
    "location": "westus",
    "name": "armclistorageGroup7062",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup7154",
    "location": "westus",
    "name": "armclistorageGroup7154",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup7265",
    "location": "westus",
    "name": "armclistorageGroup7265",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup7648",
    "location": "westus",
    "name": "armclistorageGroup7648",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup7917",
    "location": "westus",
    "name": "armclistorageGroup7917",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup8241",
    "location": "westus",
    "name": "armclistorageGroup8241",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup8275",
    "location": "westus",
    "name": "armclistorageGroup8275",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup867",
    "location": "westus",
    "name": "armclistorageGroup867",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup9079",
    "location": "westus",
    "name": "armclistorageGroup9079",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup922",
    "location": "westus",
    "name": "armclistorageGroup922",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup9343",
    "location": "westus",
    "name": "armclistorageGroup9343",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup9345",
    "location": "westus",
    "name": "armclistorageGroup9345",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup9369",
    "location": "westus",
    "name": "armclistorageGroup9369",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/armclistorageGroup9576",
    "location": "westus",
    "name": "armclistorageGroup9576",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst10658",
    "location": "westus",
    "name": "clutst10658",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst10658Destination",
    "location": "westus",
    "name": "clutst10658Destination",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst11617",
    "location": "westus",
    "name": "clutst11617",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst12131",
    "location": "westus",
    "name": "clutst12131",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst14273",
    "location": "westus",
    "name": "clutst14273",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst15898",
    "location": "westus",
    "name": "clutst15898",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst16319",
    "location": "westus",
    "name": "clutst16319",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst16367",
    "location": "westus",
    "name": "clutst16367",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst16424",
    "location": "westus",
    "name": "clutst16424",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst16599",
    "location": "westus",
    "name": "clutst16599",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst18253",
    "location": "westus",
    "name": "clutst18253",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst18832",
    "location": "westus",
    "name": "clutst18832",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst19840",
    "location": "westus",
    "name": "clutst19840",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst19876",
    "location": "westus",
    "name": "clutst19876",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst19910",
    "location": "westus",
    "name": "clutst19910",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst20217",
    "location": "westus",
    "name": "clutst20217",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst22301",
    "location": "westus",
    "name": "clutst22301",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst24285",
    "location": "westus",
    "name": "clutst24285",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst25492",
    "location": "westus",
    "name": "clutst25492",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst25492Destination",
    "location": "westus",
    "name": "clutst25492Destination",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst28055",
    "location": "westus",
    "name": "clutst28055",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst28400",
    "location": "westus",
    "name": "clutst28400",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst28769",
    "location": "westus",
    "name": "clutst28769",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst29085",
    "location": "westus",
    "name": "clutst29085",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst29333",
    "location": "westus",
    "name": "clutst29333",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst30089",
    "location": "westus",
    "name": "clutst30089",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst31207",
    "location": "westus",
    "name": "clutst31207",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst31335",
    "location": "westus",
    "name": "clutst31335",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst32303",
    "location": "westus",
    "name": "clutst32303",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst34632",
    "location": "westus",
    "name": "clutst34632",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst37223",
    "location": "westus",
    "name": "clutst37223",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst38483",
    "location": "westus",
    "name": "clutst38483",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst39112",
    "location": "westus",
    "name": "clutst39112",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst40026",
    "location": "westus",
    "name": "clutst40026",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst41390",
    "location": "westus",
    "name": "clutst41390",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst42144",
    "location": "westus",
    "name": "clutst42144",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst42144Destination",
    "location": "westus",
    "name": "clutst42144Destination",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst43083",
    "location": "westus",
    "name": "clutst43083",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst43810",
    "location": "westus",
    "name": "clutst43810",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst43963",
    "location": "westus",
    "name": "clutst43963",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst44249",
    "location": "westus",
    "name": "clutst44249",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst44935",
    "location": "westus",
    "name": "clutst44935",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst45773",
    "location": "westus",
    "name": "clutst45773",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst47034",
    "location": "westus",
    "name": "clutst47034",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst48178",
    "location": "westus",
    "name": "clutst48178",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst50877",
    "location": "westus",
    "name": "clutst50877",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst50926",
    "location": "westus",
    "name": "clutst50926",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst52016",
    "location": "westus",
    "name": "clutst52016",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst53369",
    "location": "westus",
    "name": "clutst53369",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst54011",
    "location": "westus",
    "name": "clutst54011",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {
      "testtag": "testval"
    }
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst55339",
    "location": "westus",
    "name": "clutst55339",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst55642",
    "location": "westus",
    "name": "clutst55642",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst56010",
    "location": "westus",
    "name": "clutst56010",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst56010Destination",
    "location": "westus",
    "name": "clutst56010Destination",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst57974",
    "location": "westus",
    "name": "clutst57974",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst59108",
    "location": "westus",
    "name": "clutst59108",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst59926",
    "location": "westus",
    "name": "clutst59926",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst60612",
    "location": "westus",
    "name": "clutst60612",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst62393",
    "location": "westus",
    "name": "clutst62393",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst62671",
    "location": "westus",
    "name": "clutst62671",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst63961",
    "location": "westus",
    "name": "clutst63961",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst64118",
    "location": "westus",
    "name": "clutst64118",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst64902",
    "location": "westus",
    "name": "clutst64902",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst65563",
    "location": "westus",
    "name": "clutst65563",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst65944",
    "location": "westus",
    "name": "clutst65944",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst68622",
    "location": "westus",
    "name": "clutst68622",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst69042",
    "location": "westus",
    "name": "clutst69042",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst72034",
    "location": "westus",
    "name": "clutst72034",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst72937",
    "location": "westus",
    "name": "clutst72937",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst73017",
    "location": "westus",
    "name": "clutst73017",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst73226",
    "location": "westus",
    "name": "clutst73226",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst73623",
    "location": "westus",
    "name": "clutst73623",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst74333",
    "location": "westus",
    "name": "clutst74333",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst74607",
    "location": "westus",
    "name": "clutst74607",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst75011",
    "location": "westus",
    "name": "clutst75011",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst76021",
    "location": "westus",
    "name": "clutst76021",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst76811",
    "location": "westus",
    "name": "clutst76811",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst77155",
    "location": "westus",
    "name": "clutst77155",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst78595",
    "location": "westus",
    "name": "clutst78595",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst81406",
    "location": "westus",
    "name": "clutst81406",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst82639",
    "location": "westus",
    "name": "clutst82639",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst82782",
    "location": "westus",
    "name": "clutst82782",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst83830",
    "location": "westus",
    "name": "clutst83830",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst84001",
    "location": "westus",
    "name": "clutst84001",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst84215",
    "location": "westus",
    "name": "clutst84215",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst84761",
    "location": "westus",
    "name": "clutst84761",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst85399",
    "location": "westus",
    "name": "clutst85399",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst86517",
    "location": "westus",
    "name": "clutst86517",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst86564",
    "location": "westus",
    "name": "clutst86564",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst86711",
    "location": "westus",
    "name": "clutst86711",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst88326",
    "location": "westus",
    "name": "clutst88326",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst88434",
    "location": "westus",
    "name": "clutst88434",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst88867",
    "location": "westus",
    "name": "clutst88867",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst89058",
    "location": "westus",
    "name": "clutst89058",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst89058Destination",
    "location": "westus",
    "name": "clutst89058Destination",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst89757",
    "location": "westus",
    "name": "clutst89757",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst89757Destination",
    "location": "westus",
    "name": "clutst89757Destination",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst90450",
    "location": "westus",
    "name": "clutst90450",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst90450Destination",
    "location": "westus",
    "name": "clutst90450Destination",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst92020",
    "location": "westus",
    "name": "clutst92020",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst92142",
    "location": "westus",
    "name": "clutst92142",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst93247",
    "location": "westus",
    "name": "clutst93247",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst95104",
    "location": "westus",
    "name": "clutst95104",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst96863",
    "location": "westus",
    "name": "clutst96863",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst96978",
    "location": "westus",
    "name": "clutst96978",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst97385",
    "location": "westus",
    "name": "clutst97385",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst98032",
    "location": "westus",
    "name": "clutst98032",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst98129",
    "location": "westus",
    "name": "clutst98129",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/clutst98581",
    "location": "westus",
    "name": "clutst98581",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/Default-ApplicationInsights-CentralUS",
    "location": "centralus",
    "name": "Default-ApplicationInsights-CentralUS",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/Default-Networking",
    "location": "westus",
    "name": "Default-Networking",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/Default-NotificationHubs-WestUS",
    "location": "westus",
    "name": "Default-NotificationHubs-WestUS",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/Default-ServiceBus-WestUS",
    "location": "westus",
    "name": "Default-ServiceBus-WestUS",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/Default-SQL-WestUS",
    "location": "westus",
    "name": "Default-SQL-WestUS",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/Default-Storage-WestUS",
    "location": "westus",
    "name": "Default-Storage-WestUS",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/Default-Web-WestUS",
    "location": "westus",
    "name": "Default-Web-WestUS",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/destanko-test1",
    "location": "westus",
    "name": "destanko-test1",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/destanko-test1233333",
    "location": "westus",
    "name": "destanko-test1233333",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/foozap01",
    "location": "westus",
    "name": "foozap01",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/ppppp2",
    "location": "southcentralus",
    "name": "ppppp2",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/pppppp",
    "location": "westus",
    "name": "pppppp",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/r1",
    "location": "westus",
    "name": "r1",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/testrg15109",
    "location": "westus",
    "name": "testrg15109",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/testrg16663",
    "location": "westus",
    "name": "testrg16663",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/testrg18579",
    "location": "westus",
    "name": "testrg18579",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/testrg8559",
    "location": "westus",
    "name": "testrg8559",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": null
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xplattestadla7278",
    "location": "southcentralus",
    "name": "xplattestadla7278",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xplatTestGCreate1218",
    "location": "westus",
    "name": "xplatTestGCreate1218",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xplatTestGCreate3656",
    "location": "westus",
    "name": "xplatTestGCreate3656",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xplatTestGCreateDns2167",
    "location": "westus",
    "name": "xplatTestGCreateDns2167",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xplatTestGCreateDns7046",
    "location": "westus",
    "name": "xplatTestGCreateDns7046",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xplatTestGCreateLbNat3",
    "location": "westus",
    "name": "xplatTestGCreateLbNat3",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xplatTestGExpressRoute3509",
    "location": "westus",
    "name": "xplatTestGExpressRoute3509",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xplatTestGExtension5940",
    "location": "eastus",
    "name": "xplatTestGExtension5940",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {
      "arm-cli-vm-extension-tests": "2016-02-29T08:05:18.907Z"
    }
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xplatTestGExtension9085",
    "location": "southeastasia",
    "name": "xplatTestGExtension9085",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {
      "arm-cli-vm-extension-tests": "2016-01-21T23:38:57.711Z"
    }
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xplatTestGroupGatewayCon7412",
    "location": "westus",
    "name": "xplatTestGroupGatewayCon7412",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xplatTestGSz6241",
    "location": "eastus",
    "name": "xplatTestGSz6241",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {
      "arm-cli-vm-sizes-tests": "2016-02-02T13:11:46.487Z"
    }
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xplatTestGVMDocker2951",
    "location": "eastus",
    "name": "xplatTestGVMDocker2951",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {
      "arm-cli-vm-docker-tests": "2016-02-18T16:05:48.920Z"
    }
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xplatTestGVMDocker6705",
    "location": "eastus",
    "name": "xplatTestGVMDocker6705",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {
      "arm-cli-vm-docker-tests": "2016-02-29T12:20:36.945Z"
    }
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource1531",
    "location": "westus",
    "name": "xTestResource1531",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource1730",
    "location": "westus",
    "name": "xTestResource1730",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource194",
    "location": "westus",
    "name": "xTestResource194",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource2039",
    "location": "westus",
    "name": "xTestResource2039",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource2660",
    "location": "westus",
    "name": "xTestResource2660",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource318",
    "location": "southcentralus",
    "name": "xTestResource318",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource3362",
    "location": "westus",
    "name": "xTestResource3362",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource3559",
    "location": "westus",
    "name": "xTestResource3559",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource4219",
    "location": "westus",
    "name": "xTestResource4219",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource475",
    "location": "westus",
    "name": "xTestResource475",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource5203",
    "location": "westus",
    "name": "xTestResource5203",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource5515",
    "location": "westus",
    "name": "xTestResource5515",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource723",
    "location": "southcentralus",
    "name": "xTestResource723",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource7252",
    "location": "westus",
    "name": "xTestResource7252",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource7909",
    "location": "westus",
    "name": "xTestResource7909",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource811",
    "location": "westus",
    "name": "xTestResource811",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource9256",
    "location": "westus",
    "name": "xTestResource9256",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource9641",
    "location": "westus",
    "name": "xTestResource9641",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/xTestResource9737",
    "location": "westus",
    "name": "xTestResource9737",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  },
  {
    "id": "/subscriptions/0b1f6471-1bf0-4dda-aec3-cb9272f09590/resourceGroups/ygvmgroup",
    "location": "westus",
    "name": "ygvmgroup",
    "properties": {
      "provisioningState": "Succeeded"
    },
    "tags": {}
  }
]
"""
    },
]
