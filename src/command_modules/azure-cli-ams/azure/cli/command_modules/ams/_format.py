

def get_sp_create_output_xml(result):
    return print('\n'.join(['<add key=\"{}\" value=\"{}\" />'.format(k, v) for k, v in result.items()]))