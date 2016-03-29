import requests
import re
from pip import get_installed_distributions
from pip._vendor.packaging import version as packaging_version

class UpdateCheckError(Exception):
    '''Raised when there is an error attempting to check for update(s)
    '''
    pass

def _get_latest_version_private(pkg_name):
    """Check for an update to the component from project private PyPI server"""
    response = requests.get('http://40.112.211.51:8080/simple/'+pkg_name)
    if response.status_code != 200:
        raise UpdateCheckError('PyPI returned status code {}.'.format(response.status_code))
    # Parse the package links from the response
    pattern_package_links = re.compile(r'href=[\'"]?([^#\'" >]+)')
    package_links = re.findall(pattern_package_links, response.text)
    # Get the package versions from the links
    search_start = '/packages/'+pkg_name+'-'
    search_end = '.tar.gz'
    pattern_version = re.compile('%s(.*)%s' % (search_start, search_end))
    versions = [re.search(pattern_version, pl).group(1) for pl in package_links]
    # Parse the versions so they can be sorted
    parsed_versions = [packaging_version.parse(v) for v in versions
                       if not packaging_version.parse(v).is_prerelease]
    sorted_versions = sorted(parsed_versions)
    latest_version = sorted_versions[-1] if sorted_versions else None
    return latest_version

def _get_latest_version_public(pkg_name):
    """Check for an update to the component from PyPI"""
    # TODO This hasn't been tested fully since our packages aren't on PyPI
    response = requests.get('https://pypi.python.org/pypi/{0}/json'.format(pkg_name))
    if response.status_code != 200:
        raise UpdateCheckError('PyPI returned status code {}.'.format(response.status_code))
    response_json = response.json()
    if not response_json or not response_json['releases']:
        raise UpdateCheckError('Unable to get version info from PyPI.')
    parsed_versions = [packaging_version.parse(v) for v in response_json['releases']
                if not packaging_version.parse(v).is_prerelease]
    sorted_versions = sorted(parsed_versions)
    # latest version is last in sorted list
    return sorted_versions[-1] if sorted_versions else None

def _get_current_version(pkg_name):
    current_dist = [dist for dist in get_installed_distributions(local_only=True)
                    if dist.key == pkg_name]
    if not current_dist:
        raise UpdateCheckError("Component not installed.")
    return packaging_version.parse(current_dist[0].version)

def _check_for_update(pkg_name, private=False):
    current_version = _get_current_version(pkg_name)
    if private:
        latest_version = _get_latest_version_private(pkg_name)
    else:
        latest_version = _get_latest_version_public(pkg_name)
    return {
        'current_version': current_version,
        'latest_version': latest_version,
        'update_available': current_version < latest_version,
    }

def check_for_cli_update(private=False):
    return _check_for_update(pkg_name='azure-cli', private=private)

def check_for_component_update(component_name, private=False):
    return _check_for_update(pkg_name='azure-cli-'+component_name, private=private)
