import re

from azure.cli.main import EVENT_DISPATCHER

@EVENT_DISPATCHER.event_handler(EVENT_DISPATCHER.TRANSFORM_RESULT)
def resource_group_transform(name, event_data):
    def parse_id(id):
        parsed = {}
        parts = re.split('/', id)
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
                    obj['resourceGroup'] = parse_id(obj['id'])['resource-group']
            except (KeyError, IndexError):
                pass
            for item_key in obj:
                add_resource_group(obj[item_key])

    add_resource_group(event_data['result'])
