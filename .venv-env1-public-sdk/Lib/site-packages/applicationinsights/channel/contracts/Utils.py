import collections

def _write_complex_object(defaults, values):
    output = collections.OrderedDict()
    for key in defaults.keys():
        default = defaults[key]
        if key in values:
            value = values[key]
            if value == None:
                value = default
        elif default:
            value = default
        else:
            continue

        if isinstance(value, list):
            value_copy = []
            for item in value:
                if hasattr(item, 'write') and callable(getattr(item, 'write')):
                    value_copy.append(item.write())
                else:
                    value_copy.append(item)
            if len(value_copy) > 0:
                output[key] = value_copy
        elif isinstance(value, dict):
            value_copy = collections.OrderedDict()
            keys = sorted(value.keys())
            for item_key in keys:
                item_value = value[item_key]
                if hasattr(item_value, 'write') and callable(getattr(item_value, 'write')):
                    value_copy[item_key] = item_value.write()
                else:
                    value_copy[item_key] = item_value
            if len(value_copy) > 0:
                output[key] = value_copy
        elif hasattr(value, 'write') and callable(getattr(value, 'write')):
            value_copy = value.write()
            if len(value_copy) > 0:
                output[key] = value_copy
        else:
            value_copy = value
            output[key] = value_copy        

    return output