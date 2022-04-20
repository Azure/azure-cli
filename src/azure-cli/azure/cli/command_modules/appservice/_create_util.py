# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

import os
import zipfile
from random import randint
from knack.util import CLIError
from knack.log import get_logger
from azure.cli.core.commands.client_factory import get_mgmt_service_client
from azure.cli.core.util import get_file_json
from azure.mgmt.web.models import SkuDescription

from ._constants import (NETCORE_RUNTIME_NAME, NODE_RUNTIME_NAME, ASPDOTNET_RUNTIME_NAME, STATIC_RUNTIME_NAME,
                         PYTHON_RUNTIME_NAME, LINUX_SKU_DEFAULT, OS_DEFAULT, DOTNET_RUNTIME_NAME,
                         DOTNET_TARGET_FRAMEWORK_REGEX, GENERATE_RANDOM_APP_NAMES)
from .utils import get_resource_if_exists

logger = get_logger(__name__)


def _resource_client_factory(cli_ctx, **_):
    from azure.cli.core.profiles import ResourceType
    return get_mgmt_service_client(cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES)


def web_client_factory(cli_ctx, **_):
    from azure.mgmt.web import WebSiteManagementClient
    return get_mgmt_service_client(cli_ctx, WebSiteManagementClient)


def zip_contents_from_dir(dirPath, lang):
    import tempfile
    import uuid
    relroot = os.path.abspath(tempfile.gettempdir())
    path_and_file = os.path.splitdrive(dirPath)[1]
    file_val = os.path.split(path_and_file)[1]
    file_val_unique = file_val + str(uuid.uuid4())[:259]
    zip_file_path = relroot + os.path.sep + file_val_unique + ".zip"
    abs_src = os.path.abspath(dirPath)
    try:
        with zipfile.ZipFile("{}".format(zip_file_path), "w", zipfile.ZIP_DEFLATED) as zf:
            for dirname, subdirs, files in os.walk(dirPath):
                # skip node_modules folder for Node apps,
                # since zip_deployment will perform the build operation
                if lang.lower() == NODE_RUNTIME_NAME:
                    subdirs[:] = [d for d in subdirs if 'node_modules' not in d]
                elif lang.lower() == NETCORE_RUNTIME_NAME:
                    subdirs[:] = [d for d in subdirs if d not in ['obj', 'bin']]
                elif lang.lower() == PYTHON_RUNTIME_NAME:
                    subdirs[:] = [d for d in subdirs if 'env' not in d]  # Ignores dir that contain env

                    filtered_files = []
                    for filename in files:
                        if filename == '.env':
                            logger.info("Skipping file: %s/%s", dirname, filename)
                        else:
                            filtered_files.append(filename)
                    files[:] = filtered_files

                for filename in files:
                    absname = os.path.abspath(os.path.join(dirname, filename))
                    arcname = absname[len(abs_src) + 1:]
                    zf.write(absname, arcname)
    except IOError as e:
        if e.errno == 13:
            raise CLIError('Insufficient permissions to create a zip in current directory. '
                           'Please re-run the command with administrator privileges')
        raise CLIError(e)

    return zip_file_path


def get_runtime_version_details(file_path, lang_name, stack_helper, is_linux=False):
    version_detected = None
    version_to_create = None

    if lang_name.lower() != STATIC_RUNTIME_NAME:
        versions = stack_helper.get_version_list(lang_name, is_linux)
        default_version = stack_helper.get_default_version(lang_name, is_linux)
        version_to_create = default_version
    if lang_name.lower() in [DOTNET_RUNTIME_NAME, ASPDOTNET_RUNTIME_NAME]:
        version_detected = parse_dotnet_version(file_path, default_version)
        version_to_create = detect_dotnet_version_tocreate(version_detected, default_version, versions)
    elif lang_name.lower() == NETCORE_RUNTIME_NAME:
        # method returns list in DESC, pick the first
        version_detected = parse_netcore_version(file_path)[0]
        version_to_create = detect_dotnet_version_tocreate(version_detected, default_version, versions)
    elif lang_name.lower() == NODE_RUNTIME_NAME:
        if file_path == '':
            version_detected = "-"
            version_to_create = default_version
        else:
            version_detected = parse_node_version(file_path)[0]
            version_to_create = detect_node_version_tocreate(version_detected, versions, default_version)
    elif lang_name.lower() == PYTHON_RUNTIME_NAME:
        version_detected = "-"
        version_to_create = default_version
    elif lang_name.lower() == STATIC_RUNTIME_NAME:
        version_detected = "-"
        version_to_create = "-"
    return {'detected': version_detected, 'to_create': version_to_create}


def create_resource_group(cmd, rg_name, location):
    from azure.cli.core.profiles import ResourceType, get_sdk
    rcf = _resource_client_factory(cmd.cli_ctx)
    resource_group = get_sdk(cmd.cli_ctx, ResourceType.MGMT_RESOURCE_RESOURCES, 'ResourceGroup', mod='models')
    rg_params = resource_group(location=location)
    return rcf.resource_groups.create_or_update(rg_name, rg_params)


def check_resource_group_exists(cmd, rg_name):
    rcf = _resource_client_factory(cmd.cli_ctx)
    return rcf.resource_groups.check_existence(rg_name)


def _check_resource_group_supports_os(cmd, rg_name, is_linux):
    # get all appservice plans from RG
    client = web_client_factory(cmd.cli_ctx)
    plans = list(client.app_service_plans.list_by_resource_group(rg_name))
    for item in plans:
        # for Linux if an app with reserved==False exists, ASP doesn't support Linux
        if is_linux and not item.reserved:
            return False
        if not is_linux and item.reserved:
            return False
    return True


def get_num_apps_in_asp(cmd, rg_name, asp_name):
    client = web_client_factory(cmd.cli_ctx)
    return len(list(client.app_service_plans.list_web_apps(rg_name, asp_name)))


# pylint:disable=unexpected-keyword-arg
def get_lang_from_content(src_path, html=False, is_linux=False):
    # NODE: package.json should exist in the application root dir
    # NETCORE & DOTNET: *.csproj should exist in the application dir
    # NETCORE: <TargetFramework>netcoreapp2.0</TargetFramework>
    # DOTNET: <TargetFrameworkVersion>v4.5.2</TargetFrameworkVersion>
    runtime_details_dict = dict.fromkeys(['language', 'file_loc', 'default_sku'])
    package_json_file = os.path.join(src_path, 'package.json')
    package_python_file = os.path.join(src_path, 'requirements.txt')
    static_html_file = ""
    package_netcore_file = ""
    runtime_details_dict['language'] = ''
    runtime_details_dict['file_loc'] = ''
    runtime_details_dict['default_sku'] = 'F1'
    import fnmatch
    for _dirpath, _dirnames, files in os.walk(src_path):
        for file in files:
            if html and (fnmatch.fnmatch(file, "*.html") or fnmatch.fnmatch(file, "*.htm") or
                         fnmatch.fnmatch(file, "*shtml.")):
                static_html_file = os.path.join(src_path, file)
                break
            if fnmatch.fnmatch(file, "*.csproj"):
                package_netcore_file = os.path.join(src_path, file)
                if not os.path.isfile(package_netcore_file):
                    package_netcore_file = os.path.join(_dirpath, file)
                break

    if html:
        if static_html_file:
            runtime_details_dict['language'] = STATIC_RUNTIME_NAME
            runtime_details_dict['file_loc'] = static_html_file
            runtime_details_dict['default_sku'] = 'F1'
        else:
            raise CLIError("The html flag was passed, but could not find HTML files, "
                           "see 'https://go.microsoft.com/fwlink/?linkid=2109470' for more information")
    elif os.path.isfile(package_python_file):
        runtime_details_dict['language'] = PYTHON_RUNTIME_NAME
        runtime_details_dict['file_loc'] = package_python_file
        runtime_details_dict['default_sku'] = LINUX_SKU_DEFAULT
    elif os.path.isfile(package_json_file) or os.path.isfile('server.js') or os.path.isfile('index.js'):
        runtime_details_dict['language'] = NODE_RUNTIME_NAME
        runtime_details_dict['file_loc'] = package_json_file if os.path.isfile(package_json_file) else ''
        runtime_details_dict['default_sku'] = LINUX_SKU_DEFAULT
    elif package_netcore_file:
        runtime_lang = detect_dotnet_lang(package_netcore_file, is_linux=is_linux)
        runtime_details_dict['language'] = runtime_lang
        runtime_details_dict['file_loc'] = package_netcore_file
        runtime_details_dict['default_sku'] = 'F1'
    else:  # TODO: Update the doc when the detection logic gets updated
        raise CLIError("Could not auto-detect the runtime stack of your app.\n"
                       "HINT: Are you in the right folder?\n"
                       "For more information, see 'https://go.microsoft.com/fwlink/?linkid=2109470'")
    return runtime_details_dict


def detect_dotnet_lang(csproj_path, is_linux=False):
    import xml.etree.ElementTree as ET
    import re

    if is_linux:
        return NETCORE_RUNTIME_NAME

    parsed_file = ET.parse(csproj_path)
    root = parsed_file.getroot()
    version_lang = ''
    version_full = ''
    for target_ver in root.iter('TargetFramework'):
        version_full = target_ver.text
        version_full = ''.join(version_full.split()).lower()
        version_lang = re.sub(r'([^a-zA-Z\s]+?)', '', target_ver.text)

    if 'netcore' in version_lang.lower():
        return NETCORE_RUNTIME_NAME
    if version_full and re.fullmatch(DOTNET_TARGET_FRAMEWORK_REGEX, version_full):
        return DOTNET_RUNTIME_NAME
    return ASPDOTNET_RUNTIME_NAME


def parse_dotnet_version(file_path, default_version):
    version_detected = [default_version]
    try:
        from xml.dom import minidom
        import re
        xmldoc = minidom.parse(file_path)
        framework_ver = xmldoc.getElementsByTagName('TargetFrameworkVersion')
        if not framework_ver:
            framework_ver = xmldoc.getElementsByTagName('TargetFramework')
        target_ver = framework_ver[0].firstChild.data
        non_decimal = re.compile(r'[^\d.]+')
        # reduce the version to '5.7.4' from '5.7'
        if target_ver is not None:
            # remove the string from the beginning of the version value
            c = non_decimal.sub('', target_ver)
            version_detected = c[:3]
    except:  # pylint: disable=bare-except
        logger.warning("Could not parse dotnet version from *.csproj. Defaulting to %s", version_detected[0])
        version_detected = version_detected[0]
    return version_detected


def parse_netcore_version(file_path):
    import xml.etree.ElementTree as ET
    import re
    version_detected = ['0.0']
    parsed_file = ET.parse(file_path)
    root = parsed_file.getroot()
    for target_ver in root.iter('TargetFramework'):
        version_detected = re.findall(r"\d+\.\d+", target_ver.text)
    # incase of multiple versions detected, return list in descending order
    version_detected = sorted(version_detected, key=float, reverse=True)
    return version_detected


def parse_node_version(file_path):
    # from node experts the node value in package.json can be found here   "engines": { "node":  ">=10.6.0"}
    import json
    import re
    version_detected = []
    with open(file_path) as data_file:
        data = json.load(data_file)
        for key, value in data.items():
            if key == 'engines' and 'node' in value:
                value_detected = value['node']
                non_decimal = re.compile(r'[^\d.]+')
                # remove the string ~ or  > that sometimes exists in version value
                c = non_decimal.sub('', value_detected)
                # reduce the version to '6.0' from '6.0.0'
                if '.' in c:  # handle version set as 4 instead of 4.0
                    num_array = c.split('.')
                    num = num_array[0] + "." + num_array[1]
                else:
                    num = c + ".0"
                version_detected.append(num)
    return version_detected or ['0.0']


def detect_dotnet_version_tocreate(detected_ver, default_version, versions_list):
    min_ver = versions_list[0]
    if detected_ver in versions_list:
        return detected_ver
    if detected_ver < min_ver:
        return min_ver
    return default_version


# TODO include better detections logic here
def detect_node_version_tocreate(detected_ver, node_versions, default_node_version):
    if detected_ver in node_versions:
        return detected_ver
    return default_node_version


def find_key_in_json(json_data, key):
    for k, v in json_data.items():
        if key in k:
            yield v
        elif isinstance(v, dict):
            for id_val in find_key_in_json(v, key):
                yield id_val


def set_location(cmd, sku, location):
    client = web_client_factory(cmd.cli_ctx)
    if location is None:
        locs = client.list_geo_regions(sku, True)
        available_locs = []
        for loc in locs:
            available_locs.append(loc.name)
        loc = available_locs[0]
    else:
        loc = location
    return loc.replace(" ", "").lower()


def get_site_availability(cmd, name):
    """ This is used by az webapp up to verify if a site needs to be created or should just be deployed"""
    client = web_client_factory(cmd.cli_ctx)
    availability = client.check_name_availability(name, 'Site')

    # check for "." in app name. it is valid for hostnames to contain it, but not allowed for webapp names
    if "." in name:
        availability.name_available = False
        availability.reason = "Invalid"
        availability.message = ("Site names only allow alphanumeric characters and hyphens, "
                                "cannot start or end in a hyphen, and must be less than 64 chars.")
    return availability


def get_app_details(cmd, name):
    client = web_client_factory(cmd.cli_ctx)
    data = (list(filter(lambda x: name.lower() == x.name.lower(), client.web_apps.list())))
    _num_items = len(data)
    if _num_items > 0:
        return data[0]
    return None


def get_rg_to_use(user, rg_name=None):
    default_rg = "{}_rg_{:04}".format(user, randint(0, 9999))
    if rg_name is not None:
        return rg_name
    return default_rg


def get_profile_username():
    from azure.cli.core._profile import Profile
    user = Profile().get_current_account_user()
    user = user.split('@', 1)[0]
    if len(user.split('#', 1)) > 1:  # on cloudShell user is in format live.com#user@domain.com
        user = user.split('#', 1)[1]
    return user


def get_sku_to_use(src_dir, html=False, sku=None, runtime=None, app_service_environment=None):
    if sku is None:
        if app_service_environment:
            return 'I1v2'
        if runtime:  # user overrided language detection by specifiying runtime
            return 'F1'
        lang_details = get_lang_from_content(src_dir, html)
        return lang_details.get("default_sku")
    logger.info("Found sku argument, skipping use default sku")
    return sku


def set_language(src_dir, html=False):
    lang_details = get_lang_from_content(src_dir, html)
    return lang_details.get('language')


def detect_os_form_src(src_dir, html=False):
    lang_details = get_lang_from_content(src_dir, html)
    language = lang_details.get('language')
    return "Linux" if language is not None and language.lower() == NODE_RUNTIME_NAME \
        or language.lower() == PYTHON_RUNTIME_NAME else OS_DEFAULT


def get_plan_to_use(cmd, user, loc, sku, create_rg, resource_group_name, client, is_linux=False, plan=None):
    _default_asp = _get_default_plan_name(user)
    if plan is None:  # --plan not provided by user
        # get the plan name to use
        return _determine_if_default_plan_to_use(cmd, _default_asp, resource_group_name, loc, sku, create_rg, is_linux)

    asp = get_resource_if_exists(client.app_service_plans, resource_group_name=resource_group_name, name=plan)
    if asp is not None:
        if asp.reserved != is_linux:
            logger.warning("Existing app service plan %s has a different OS type and deployment may fail. "
                           "Consider using a different OS or app service plan", plan)
    return plan


def _get_default_plan_name(user):
    return "{}_asp_{:04}".format(user, randint(0, 9999))


# Portal uses the current_stack property in the app metadata to display the correct stack
# This value should be one of: ['dotnet', 'dotnetcore', 'node', 'php', 'python', 'java']
def get_current_stack_from_runtime(runtime):
    language = runtime.split('|')[0].lower()
    if language == 'aspnet':
        return 'dotnet'
    return language


# if plan name not provided we need to get a plan name based on the OS, location & SKU
def _determine_if_default_plan_to_use(cmd, plan_name, resource_group_name, loc, sku, create_rg, is_linux):
    client = web_client_factory(cmd.cli_ctx)
    if create_rg:  # if new RG needs to be created use the default name
        return plan_name

    # get all ASPs in the RG & filter to the ones that contain the plan_name
    _asp_generic = plan_name[:plan_name.rindex("_")]
    _asp_list = (list(filter(lambda x: _asp_generic in x.name,
                             client.app_service_plans.list_by_resource_group(resource_group_name))))
    _num_asp = len(_asp_list)
    if _num_asp:
        # check if we have at least one app that can be used with the combination of loc, sku & os
        selected_asp = next((a for a in _asp_list if isinstance(a.sku, SkuDescription) and
                             a.sku.name.lower() == sku.lower() and
                             (a.location.replace(" ", "").lower() == loc.lower()) and
                             a.reserved == is_linux), None)
        if selected_asp is not None:
            return selected_asp.name
        # from the sorted data pick the last one & check if a new ASP needs to be created
        # based on SKU or not
        data_sorted = sorted(_asp_list, key=lambda x: x.name)
        _plan_info = data_sorted[_num_asp - 1]
        _asp_num = 1
        try:
            _asp_num = int(_plan_info.name.split('_')[-1]) + 1  # default asp created by CLI can be of type plan_num
        except ValueError:
            pass
        return '{}_{}'.format(_asp_generic, _asp_num)
    return plan_name


def should_create_new_app(cmd, rg_name, app_name):  # this is currently referenced by an extension command
    client = web_client_factory(cmd.cli_ctx)
    for item in list(client.web_apps.list_by_resource_group(rg_name)):
        if item.name.lower() == app_name.lower():
            return False
    return True


def generate_default_app_name(cmd):
    def generate_name(cmd):
        import uuid
        from random import choice

        noun = choice(get_file_json(GENERATE_RANDOM_APP_NAMES)['APP_NAME_NOUNS'])
        adjective = choice(get_file_json(GENERATE_RANDOM_APP_NAMES)['APP_NAME_ADJECTIVES'])
        random_uuid = str(uuid.uuid4().hex)

        name = '{}-{}-{}'.format(adjective, noun, random_uuid)
        name_available = get_site_availability(cmd, name).name_available

        if name_available:
            return name
        return ""

    retry_times = 5
    generated_name = generate_name(cmd)
    while not generated_name and retry_times > 0:
        retry_times -= 1
        generated_name = generate_name(cmd)

    if not generated_name:
        raise CLIError("Unable to generate a default name for webapp. Please specify webapp name using --name flag")
    return generated_name
