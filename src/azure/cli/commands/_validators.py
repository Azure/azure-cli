def validate_tags(string):
    ''' Extracts multiple tags in key[=value] format, separated by semicolons '''
    result = None
    if string:
        result = validate_key_value_pairs(string)
        s_list = [x for x in string.split(';') if '=' not in x]  # single values
        result.update(dict((x, '') for x in s_list))
    return result

def validate_tag(string):
    ''' Extracts a single tag in key[=value] format '''
    result = None
    if string:
        comps = string.split('=', 1)
        result = {comps[0]: comps[1]} if len(comps) > 1 else {string: ''}
    return result

def validate_key_value_pairs(string):
    ''' Validates key-value pairs in the following format: a=b;c=d '''
    result = None
    if string:
        kv_list = [x for x in string.split(';') if '=' in x]     # key-value pairs
        result = dict(x.split('=', 1) for x in kv_list)
    return result
