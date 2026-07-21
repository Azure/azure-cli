import logging
import uuid
import platform
from typing import Union

from ._store import Store, WindowsStore
    
def get_device_id(*, full_trace: bool = False) -> str:
    """
    Get the device id in the format 0000- from the store location or create a new one if it does not exist.
    An empty string is returned if an error occurs during saving or retrieval of the device id.
    Linux id location: $XDG_CACHE_HOME/deviceid if defined else $HOME/.cache/deviceid
    MacOS id location: $HOME/Library/Application Support/Microsoft/DeveloperTools/deviceid
    Windows id location: HKEY_CURRENT_USER\\SOFTWARE\\Microsoft\\DeveloperTools\\deviceid
    :keyword full_trace: If True, the full stack trace is logged. Default is False.
    :return: The device id.
    :rtype: str
    """

    device_id: str = ""
    store: Union[Store, WindowsStore]
    
    try:
        if platform.system() == 'Windows':
            store = WindowsStore()
        elif platform.system() in ('Linux','Darwin'):
            store = Store()
        else:
            return device_id
        device_id = store.retrieve_id()
        return device_id
    except (PermissionError, ValueError, NotImplementedError) as ferr:
        if full_trace:
            logging.getLogger(__name__).exception(ferr)
        return device_id
    except Exception as e:
        if full_trace:
            logging.getLogger(__name__).exception(e)

    device_id = str(uuid.uuid4()).lower()

    try:
        store.store_id(device_id)
    except Exception as e:
        if full_trace:
            logging.getLogger(__name__).exception(e)
        device_id = ""

    return device_id
