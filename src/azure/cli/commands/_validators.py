def validate_tags(string):
    ''' Validates the string containers only key-value pairs and single
    tags in the format: a=b;c '''
    result = None
    if string:
        result = validate_key_value_pairs(string)
        s_list = [x for x in string.split(';') if '=' not in x]  # single values
        result.update(dict((x, '') for x in s_list))
    return result

def validate_key_value_pairs(string):
    ''' Validates key-value pairs in the following format: a=b;c=d '''
    result = None
    if string:
        kv_list = [x for x in string.split(';') if '=' in x]     # key-value pairs
        result = dict(x.split('=', 1) for x in kv_list)
    return result
