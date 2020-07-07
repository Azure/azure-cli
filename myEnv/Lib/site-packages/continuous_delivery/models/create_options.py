from msrest.serialization import Model

class CreateOptions(Model):
    _attribute_map = {
        'app_service_plan_name': {'key': 'appServicePlanName', 'type': 'str'},
        'app_service_pricing_tier': {'key': 'appServicePricingTier', 'type': 'str'},
        'base_app_service_name': {'key': 'baseAppServiceName', 'type': 'str'}
    }

    def __init__(self, app_service_plan_name=None, app_service_pricing_tier=None, base_app_service_name=None):
        self.app_service_plan_name = app_service_plan_name
        self.app_service_pricing_tier = app_service_pricing_tier
        self.base_app_service_name = base_app_service_name