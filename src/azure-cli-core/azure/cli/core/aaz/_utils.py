import importlib


def _get_profile_pkg(aaz_module_name, cloud):
    profile_module_name = cloud.profile.lower().replace('-', '_')
    try:
        return importlib.import_module(f'{aaz_module_name}.{profile_module_name}')
    except ModuleNotFoundError:
        return None
