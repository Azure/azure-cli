import re

def register(event_dispatcher):
    def resource_group_transform(event_data):
        def parse_id(strid):
            parsed = {}
            parts = re.split('/', strid)
            parsed['resource-group'] = parts[4]
            parsed['name'] = parts[8]
            return parsed

        def add_resource_group(obj):
            if isinstance(obj, list):
                for array_item in obj:
                    add_resource_group(array_item)
            elif isinstance(obj, dict):
                try:
                    if 'resourceGroup' not in obj:
                        if obj['id']:
                            obj['resourceGroup'] = parse_id(obj['id'])['resource-group']
                except (KeyError, IndexError):
                    pass
                for item_key in obj:
                    add_resource_group(obj[item_key])

        add_resource_group(event_data['result'])
    event_dispatcher.register('TransformResult', resource_group_transform)
