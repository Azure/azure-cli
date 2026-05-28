# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------


import json
import threading
import sys
import uuid
import time
import re
import textwrap
import websocket
import requests
from azure.cli.core.azclierror import UnclassifiedUserFault
from azure.cli.core.azclierror import ResourceNotFoundError
from azure.cli.core.azclierror import AzureConnectionError
from azure.cli.core.azclierror import ForbiddenError
from azure.cli.core._profile import Profile
from azure.core.exceptions import ResourceNotFoundError as ComputeClientResourceNotFoundError
from azext_serialconsole._client_factory import _compute_client_factory
from azext_serialconsole._client_factory import cf_serialconsole
from azext_serialconsole._client_factory import cf_serial_port


# pylint: disable=too-few-public-methods
# pylint: disable=too-many-instance-attributes
class GlobalVariables:
    def __init__(self):
        self.websocket_instance = None
        self.terminal_instance = None
        self.serial_console_instance = None
        self.terminating_app = False
        self.loading = True
        self.first_message = True
        self.block_print = False
        self.trycount = 0
        self.os_is_windows = False


class PrintClass:
    CYAN = 36
    YELLOW = 33
    RED = 91

    def __init__(self):
        self.message_buffer = ""

    def print(self, message, color=None, buffer=True):
        if color:
            message = "\x1b[" + str(color) + "m" + message + "\x1b[0m"
        if GV.block_print and buffer:
            self.message_buffer += message
        else:
            if not GV.block_print:
                self.empty_message_buffer()
            print(message, end="", flush=True)

    def clear_screen(self, buffer=True):
        self.print("\x1b[2J\x1b[0;0H", buffer=buffer)

    def clear_line(self, buffer=True):
        self.print("\x1b[2K\x1b[1G", buffer=buffer)

    def cursor_up(self, buffer=True):
        self.print("\x1b[A", buffer=buffer)

    def set_cursor_horizontal_position(self, col, buffer=True):
        self.print("\x1b[" + str(col) + "G", buffer=buffer)

    def empty_message_buffer(self):
        print(self.message_buffer, end="", flush=True)
        self.message_buffer = ""

    def get_cursor_position(self, getch):
        self.print("\x1b[6n", buffer=False)
        buf = ""
        while True:
            c = getch().decode()
            buf += c
            if c == "R":
                break
        try:
            matches = re.match(r"^\x1b\[(\d*);(\d*)R", buf)
            groups = matches.groups()
        except AttributeError:
            return 1, 1
        return int(groups[0]), int(groups[1])

    def get_terminal_width(self, getch):
        self.hide_cursor(buffer=False)
        _, original_col = self.get_cursor_position(getch)
        self.set_cursor_horizontal_position(999, buffer=False)
        _, width = self.get_cursor_position(getch)
        self.set_cursor_horizontal_position(original_col, buffer=False)
        self.show_cursor(buffer=False)
        return width

    def hide_cursor(self, buffer=True):
        self.print("\x1b[?25l", buffer=buffer)

    def show_cursor(self, buffer=True):
        self.print("\x1b[?25h", buffer=buffer)

    @staticmethod
    def _get_max_width_of_string(s):
        max_width = -1
        curr_width = 0
        i = 0
        while i < len(s):
            if s[i] == '\r' or s[i] == '\n':
                i += 2
                max_width = max(curr_width, max_width)
                curr_width = 0
            else:
                i += 1
                curr_width += 1
        return max(max_width, curr_width)

    def prompt(self, getch, message):
        GV.block_print = True
        width = self.get_terminal_width(getch)
        _, col = self.get_cursor_position(getch)
        # adjust message if it is too wide to fit in console
        if width < self._get_max_width_of_string(message):
            wrapped = textwrap.wrap(message.replace(
                "\r\n", " ").replace("\n\r", " "), width=width)
            message = "\r\n".join(wrapped)
        lines = message.count("\r\n") + message.count("\n\r") + 1
        self.print("\r\n" + message, color=PrintClass.YELLOW, buffer=False)
        c = getch()
        self.hide_cursor(buffer=False)
        for _ in range(lines):
            # self.clear_line(buffer=False)
            self.cursor_up(buffer=False)
        self.set_cursor_horizontal_position(col, buffer=False)
        self.show_cursor(buffer=False)
        self.empty_message_buffer()
        GV.block_print = False
        return c


def quitapp(from_websocket=False, message="", error_message=None, error_recommendation=None, error_func=None):
    PC.print(message + "\r\n", color=PrintClass.RED)
    GV.terminating_app = True
    GV.loading = False
    if GV.terminal_instance:
        GV.terminal_instance.revert_terminal()
        GV.terminal_instance = None
    if not from_websocket and GV.websocket_instance:
        GV.websocket_instance.close()
        GV.websocket_instance = None
    if error_message and error_func:
        raise error_func(error_message, error_recommendation)
    sys.exit()


GV = GlobalVariables()
PC = PrintClass()


# pylint: disable=too-few-public-methods
class _Getch:
    def __init__(self):
        if sys.platform.startswith('win'):
            import ctypes
            from ctypes import wintypes
            STD_INPUT_HANDLE = -10
            self.h_in = ctypes.windll.kernel32.GetStdHandle(STD_INPUT_HANDLE)
            self.lp_buffer = ctypes.create_string_buffer(1)
            self.lp_number_of_chars_read = wintypes.DWORD()
            self.n_number_of_chars_to_read = wintypes.DWORD()
            self.n_number_of_chars_to_read.value = 1
            self.impl = self._getch_windows
        else:
            self.impl = self._getch_unix

    def __call__(self):
        return self.impl()

    @staticmethod
    def _getch_unix():
        return sys.stdin.read(1).encode()

    def _getch_windows(self):
        import ctypes
        status = ctypes.windll.kernel32.ReadConsoleW(self.h_in,
                                                     self.lp_buffer,
                                                     self.n_number_of_chars_to_read,
                                                     ctypes.byref(
                                                         self.lp_number_of_chars_read),
                                                     None)
        if status == 0:
            quitapp()
        return chr(self.lp_buffer.raw[0]).encode()


class Terminal:
    ERROR_MESSAGE = "Unable to configure terminal."
    RECOMMENDATION = ("Make sure that app in running in a terminal on a Windows 10 "
                      "or Unix based machine. Versions earlier than Windows 10 are not supported.")

    def __init__(self):
        self.win_original_out_mode = None
        self.win_original_in_mode = None
        self.win_out = None
        self.win_in = None
        self.unix_original_mode = None

    def configure_terminal(self):
        if sys.platform.startswith('win'):
            import colorama
            import ctypes
            from ctypes import wintypes
            colorama.deinit()
            ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
            ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200
            ENABLE_ECHO_INPUT = 0x0004
            ENABLE_LINE_INPUT = 0x0002
            ENABLE_PROCESSED_INPUT = 0x0001
            STD_OUTPUT_HANDLE = -11
            STD_INPUT_HANDLE = -10
            DISABLE = ~(ENABLE_ECHO_INPUT | ENABLE_LINE_INPUT |
                        ENABLE_PROCESSED_INPUT)

            kernel32 = ctypes.windll.kernel32
            dw_original_out_mode = wintypes.DWORD()
            dw_original_in_mode = wintypes.DWORD()
            self.win_out = kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
            self.win_in = kernel32.GetStdHandle(STD_INPUT_HANDLE)
            if (not kernel32.GetConsoleMode(self.win_out, ctypes.byref(dw_original_out_mode)) or
                    not kernel32.GetConsoleMode(self.win_in, ctypes.byref(dw_original_in_mode))):
                quitapp(error_message=Terminal.ERROR_MESSAGE,
                        error_recommendation=Terminal.RECOMMENDATION, error_func=UnclassifiedUserFault)

            self.win_original_out_mode = dw_original_out_mode.value
            self.win_original_in_mode = dw_original_in_mode.value

            dw_out_mode = self.win_original_out_mode | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            dw_in_mode = (self.win_original_in_mode |
                          ENABLE_VIRTUAL_TERMINAL_INPUT) & DISABLE

            if (not kernel32.SetConsoleMode(self.win_out, dw_out_mode) or
                    not kernel32.SetConsoleMode(self.win_in, dw_in_mode)):
                quitapp(error_message=Terminal.ERROR_MESSAGE,
                        error_recommendation=Terminal.RECOMMENDATION, error_func=UnclassifiedUserFault)
        else:
            try:
                import tty
                import termios  # pylint: disable=import-error
                fd = sys.stdin.fileno()
            except (ModuleNotFoundError, ValueError):
                quitapp(error_message=Terminal.ERROR_MESSAGE,
                        error_recommendation=Terminal.RECOMMENDATION, error_func=UnclassifiedUserFault)

            self.unix_original_mode = termios.tcgetattr(fd)
            tty.setraw(fd)

    def revert_terminal(self):
        if sys.platform.startswith('win'):
            import ctypes
            kernel32 = ctypes.windll.kernel32
            if self.win_original_out_mode:
                kernel32.SetConsoleMode(self.win_out, self.win_original_out_mode)
            if self.win_original_in_mode:
                kernel32.SetConsoleMode(self.win_in, self.win_original_in_mode)
        else:
            if self.unix_original_mode:
                import termios  # pylint: disable=import-error
                try:
                    fd = sys.stdin.fileno()
                except ValueError:
                    return
                termios.tcsetattr(fd, termios.TCSADRAIN, self.unix_original_mode)


class SerialConsole:
    def __init__(self, cmd, resource_group_name, vm_vmss_name, vmss_instanceid):
        _, storage_account_region = get_region_from_storage_account(cmd.cli_ctx, resource_group_name,
                                                                    vm_vmss_name, vmss_instanceid)
        if storage_account_region is not None:
            kwargs = {'storage_account_region': storage_account_region}
        else:
            kwargs = {}
        client = cf_serial_port(cmd.cli_ctx, **kwargs)
        if vmss_instanceid is None:
            self.connect_func = lambda: client.connect(
                resource_group_name=resource_group_name,
                resource_provider_namespace="Microsoft.Compute",
                parent_resource_type="virtualMachines",
                parent_resource=vm_vmss_name,
                serial_port="0").connection_string
        else:
            self.connect_func = lambda: client.connect(
                resource_group_name=resource_group_name,
                resource_provider_namespace="Microsoft.Compute",
                parent_resource_type="virtualMachineScaleSets",
                parent_resource=f"{vm_vmss_name}/virtualMachines/{vmss_instanceid}",
                serial_port="0").connection_string

        self.websocket_url = None
        self.access_token = None

    @staticmethod
    def listen_for_keys():
        getch = _Getch()
        while True:
            c = getch()
            if GV.websocket_instance and not GV.first_message:
                if c == b'\x1d':
                    if GV.os_is_windows:
                        message = ("| Press n for NMI | r to Reset VM |\r\n"
                                   "| q to quit Console | CTRL + ] to forward input |")
                    else:
                        message = ("| Press n for NMI | s for SysRq | r to Reset VM |\r\n"
                                   "| q to quit Console | CTRL + ] to forward input |")
                    c = PC.prompt(getch, message)
                    if c == b'n':
                        message = ("Warning: A Non-Maskable Interrupt (NMI) is used in debugging\r\n"
                                   "scenarios and is designed to crash your target Virtual Machine.\r\n"
                                   "Are you sure you want to send an NMI? (Y/n): ")
                        c = PC.prompt(getch, message)
                        if c == b"Y":
                            GV.serial_console_instance.send_nmi()
                        continue
                    if c == b'r':
                        message = ("Warning: This results in a hard restart, like powering the computer\r\n"
                                   "down, then back up again. This can result in data loss in the virtual\r\n"
                                   "machine. You should only perform this operation if a graceful restart\r\n"
                                   "is not effective.\r\n"
                                   "Are you sure you want to Hard Reset the VM? (Y/n): ")
                        c = PC.prompt(getch, message)
                        if c == b"Y":
                            GV.serial_console_instance.send_reset()
                        continue
                    if not GV.os_is_windows and c == b's':
                        message = "Which SysRq command would you like to send? Press h for help: "
                        c = PC.prompt(getch, message)
                        GV.serial_console_instance.send_sys_rq(c.decode())
                        continue
                    if c == b'q':
                        quitapp()
                        return
                    if c != b'\x1d':
                        continue
                try:
                    if GV.websocket_instance:
                        GV.websocket_instance.send(c)
                except (AttributeError, websocket.WebSocketConnectionClosedException):
                    pass
            else:
                if c == b'\r' and not GV.loading:
                    GV.serial_console_instance.connect()
                elif c == b'\x1d':
                    c = PC.prompt(getch, "| Press q to quit Console |")
                    if c == b'q':
                        quitapp()
                        return

    @staticmethod
    def connect_loading_message_linux():
        PC.clear_screen()
        PC.print("For more information on the Azure Serial Console, see <https://aka.ms/serialconsolelinux>.\r\n",
                 color=PrintClass.YELLOW)
        indx = 0
        number_of_squares = 3
        chars = ["\u25A1"] * number_of_squares
        while GV.loading:
            PC.hide_cursor()
            chars_copy = chars.copy()
            chars_copy[indx] = "\u25A0"
            squares = " ".join(chars_copy)
            PC.clear_line()
            PC.print("Connecting to console of VM   " +
                     squares, color=PrintClass.CYAN)
            PC.show_cursor()
            indx = (indx + 1) % number_of_squares
            time.sleep(0.5)

    @staticmethod
    def connect_loading_message_windows():
        PC.clear_screen()
        message1 = ("Windows Serial Console requires Special Administration Console (SAC) to be enabled within "
                    "the Windows VM.\r\nIf you do not see SAC> in the console below after the connection is made, "
                    "SAC is not enabled.\r\n\r\n")
        message2 = ("For more information on the Azure Serial Console and SAC, "
                    "see <https://aka.ms/serialconsolewindows>.\r\n")
        PC.print(message1)
        PC.print(message2, color=PrintClass.YELLOW)
        indx = 0
        number_of_squares = 3
        chars = ["\u25A1"] * number_of_squares
        while GV.loading:
            PC.hide_cursor()
            chars_copy = chars.copy()
            chars_copy[indx] = "\u25A0"
            squares = " ".join(chars_copy)
            PC.clear_line()
            PC.print("Connecting to console of VM   " +
                     squares, color=PrintClass.CYAN)
            PC.show_cursor()
            indx = (indx + 1) % number_of_squares
            time.sleep(0.5)

    @staticmethod
    def send_loading_message(loading_text):
        indx = 0
        number_of_squares = 3
        chars = ["\u25A1"] * number_of_squares
        while GV.loading:
            chars_copy = chars.copy()
            chars_copy[indx] = "\u25A0"
            squares = " ".join(chars_copy)
            print(loading_text + "   " + squares, end="\r")
            indx = (indx + 1) % number_of_squares
            time.sleep(0.5)

    # Returns True if successful, False otherwise
    def load_websocket_url(self):
        token_info, _, _ = Profile().get_raw_token()
        self.access_token = token_info[1]
        try:
            self.websocket_url = self.connect_func()
        except:  # pylint: disable=bare-except
            return False
        return True

    def connect(self):
        def on_open(_):
            if self.new_auth_flow == "1":
                GV.websocket_instance.send(self.access_token)

        def on_message(_, message):
            if GV.first_message:
                GV.websocket_instance.send(self.access_token)
                GV.first_message = False
                GV.loading = False
                PC.clear_screen()
            else:
                PC.print(message)

        def on_error(*_):
            pass

        def on_close(_):
            GV.loading = False
            if not GV.terminating_app:
                if GV.first_message:
                    message = ("\r\nCould not establish connection to VM or VMSS. "
                               "Make sure that it is powered on and press \"Enter\" try again...")
                    PC.print(message, color=PrintClass.RED)
                else:
                    PC.print(
                        "\r\nConnection Closed: Press \"Enter\" to reconnect...", color=PrintClass.RED)
                GV.websocket_instance = None

        def connect_thread():
            if self.load_websocket_url():
                GV.websocket_instance = websocket.WebSocketApp(
                    self.websocket_url,
                    on_open=on_open,
                    on_message=on_message,
                    on_error=on_error,
                    on_close=on_close)
                GV.websocket_instance.run_forever(skip_utf8_validation=True)
            else:
                GV.loading = False
                message = ("\r\nAn unexpected error occurred. Could not establish connection to VM or VMSS. "
                           "Check network connection and press \"Enter\" to try again...")
                PC.print(message, color=PrintClass.RED)

        GV.loading = True
        GV.first_message = True

        if GV.os_is_windows:
            th1 = threading.Thread(
                target=self.connect_loading_message_windows, args=())
        else:
            th1 = threading.Thread(
                target=self.connect_loading_message_linux, args=())
        th1.daemon = True
        th1.start()

        th2 = threading.Thread(target=connect_thread, args=())
        th2.daemon = True
        th2.start()

    def launch_console(self):
        GV.terminal_instance = Terminal()
        GV.terminal_instance.configure_terminal()
        th = threading.Thread(target=self.listen_for_keys, args=())
        th.daemon = True
        th.start()
        self.connect()
        th.join()

    def send_admin_command(self, command, commandParameters):
        if self.websocket_url and self.access_token:
            url = self.websocket_url.replace("wss", "https").replace(
                "ws", "http").replace("/client", "/adminCommand/" + command)
            headers = {'accept': "application/json",
                       'authorization': "Bearer " + self.access_token,
                       'accept-language': "en",
                       'content-type': "application/json"}
            data = {'command': command,
                    'requestId': str(uuid.uuid4()),
                    'commandParameters': commandParameters}
            result = requests.post(url, headers=headers, data=json.dumps(data))
            return result.status_code == 200
        return False

    def send_nmi(self):
        return self.send_admin_command("nmi", {})

    def send_reset(self):
        return self.send_admin_command("reset", {})

    def send_sys_rq(self, key):
        return self.send_admin_command("sysrq", {"SysRqCommand": key})

    def connect_and_send_admin_command(self, command, arg_characters=None):
        if command == "nmi":
            func = self.send_nmi
            success_message = "NMI sent successfully    \r\n"
            failure_message = "Failed to send NMI       \r\n"
            loading_text = "Sending NMI to VM"
        elif command == "reset":
            func = self.send_reset
            success_message = "Successfully Hard Reset VM      \r\n"
            failure_message = "Failed to Hard Reset VM         \r\n"
            loading_text = "Forcing VM to Hard Reset"
        elif command == "sysrq" and arg_characters is not None:
            def wrapper():
                return self.send_sys_rq(arg_characters)

            func = wrapper
            success_message = "Successfully sent SysRq command\r\n"
            failure_message = "Failed to send SysRq command. Make sure the input only contains numbers and letters.\r\n"
            loading_text = "Sending SysRq to VM"
        else:
            return

        GV.loading = True

        th1 = threading.Thread(
            target=self.send_loading_message, args=(loading_text,))
        th1.daemon = True
        th1.start()

        if self.load_websocket_url():
            def on_message(ws, _):
                GV.trycount += 1
                if GV.first_message:
                    ws.send(self.access_token)
                    GV.first_message = False
                if func():
                    GV.loading = False
                    GV.terminating_app = True
                    print(success_message, end="")
                    ws.close()
                elif GV.trycount >= 2:
                    GV.loading = False
                    GV.terminating_app = True
                    print(failure_message, end="")
                    ws.close()

            wsapp = websocket.WebSocketApp(
                self.websocket_url, on_message=on_message)
            wsapp.run_forever()
            GV.loading = False
            if GV.trycount == 0:
                error_message = "Could not establish connection to VM or VMSS."
                recommendation = 'Try restarting it with "az vm restart".'
                raise AzureConnectionError(
                    error_message, recommendation=recommendation)
        else:
            GV.loading = False
            error_message = "An unexpected error occurred. Could not establish connection to VM or VMSS."
            recommendation = "Check network connection and try again."
            raise ResourceNotFoundError(
                error_message, recommendation=recommendation)


def check_serial_console_enabled(cli_ctx, storage_account_region=None):
    if storage_account_region is not None:
        kwargs = {'storage_account_region': storage_account_region}
    else:
        kwargs = {}
    client = cf_serialconsole(cli_ctx, **kwargs)
    result = client.get_console_status().additional_properties
    if ("properties" in result and "disabled" in result["properties"] and
            not result["properties"]["disabled"]):
        return
    error_message = "Azure Serial Console is not enabled for this subscription."
    recommendation = 'Enable Serial Console with "az serial-console enable".'
    raise ForbiddenError(error_message, recommendation=recommendation)


def check_resource(cli_ctx, resource_group_name, vm_vmss_name, vmss_instanceid):
    result, storage_account_region = get_region_from_storage_account(cli_ctx, resource_group_name, vm_vmss_name,
                                                                     vmss_instanceid)
    check_serial_console_enabled(cli_ctx, storage_account_region)

    if vmss_instanceid:
        if 'osName' in result.additional_properties and "windows" in result.additional_properties['osName'].lower():
            GV.os_is_windows = True

        power_state = ','.join(
            [s.display_status for s in result.statuses if s.code.startswith('PowerState/')]).lower()
        if "deallocating" in power_state or "deallocated" in power_state:
            error_message = "Azure Serial Console requires a virtual machine to be running."
            recommendation = 'Use "az vmss start" to start the Virtual Machine.'
            raise AzureConnectionError(
                error_message, recommendation=recommendation)
    else:
        if (result.instance_view is not None and
                result.instance_view.os_name is not None and
                "windows" in result.instance_view.os_name.lower()):
            GV.os_is_windows = True
        if (result.storage_profile is not None and
                result.storage_profile.image_reference is not None and
                result.storage_profile.image_reference.offer is not None and
                "windows" in result.storage_profile.image_reference.offer.lower()):
            GV.os_is_windows = True

        power_state = ','.join(
            [s.display_status for s in result.instance_view.statuses if s.code.startswith('PowerState/')])
        if "deallocating" in power_state or "deallocated" in power_state:
            error_message = "Azure Serial Console requires a virtual machine to be running."
            recommendation = 'Use "az vm start" to start the Virtual Machine.'
            raise AzureConnectionError(
                error_message, recommendation=recommendation)


def connect_serialconsole(cmd, resource_group_name, vm_vmss_name, vmss_instanceid=None):
    check_resource(cmd.cli_ctx, resource_group_name,
                   vm_vmss_name, vmss_instanceid)
    GV.serial_console_instance = SerialConsole(
        cmd, resource_group_name, vm_vmss_name, vmss_instanceid)
    GV.serial_console_instance.launch_console()


def send_nmi_serialconsole(cmd, resource_group_name, vm_vmss_name, vmss_instanceid=None):
    check_resource(cmd.cli_ctx, resource_group_name,
                   vm_vmss_name, vmss_instanceid)
    GV.serial_console_instance = SerialConsole(
        cmd, resource_group_name, vm_vmss_name, vmss_instanceid)
    GV.serial_console_instance.connect_and_send_admin_command("nmi")


def send_reset_serialconsole(cmd, resource_group_name, vm_vmss_name, vmss_instanceid=None):
    check_resource(cmd.cli_ctx, resource_group_name,
                   vm_vmss_name, vmss_instanceid)
    GV.serial_console_instance = SerialConsole(
        cmd, resource_group_name, vm_vmss_name, vmss_instanceid)
    GV.serial_console_instance.connect_and_send_admin_command("reset")


def send_sysrq_serialconsole(cmd, resource_group_name, vm_vmss_name, sysrqinput, vmss_instanceid=None):
    check_resource(cmd.cli_ctx, resource_group_name,
                   vm_vmss_name, vmss_instanceid)
    if GV.os_is_windows:
        error_message = "You can only send a SysRq to a Linux VM."
        raise ForbiddenError(error_message)
    GV.serial_console_instance = SerialConsole(
        cmd, resource_group_name, vm_vmss_name, vmss_instanceid)
    GV.serial_console_instance.connect_and_send_admin_command(
        "sysrq", arg_characters=sysrqinput)


def enable_serialconsole(cmd):
    client = cf_serialconsole(cmd.cli_ctx)
    return client.enable_console()


def disable_serialconsole(cmd):
    client = cf_serialconsole(cmd.cli_ctx)
    return client.disable_console()


def get_region_from_storage_account(cli_ctx, resource_group_name, vm_vmss_name, vmss_instanceid):
    from azext_serialconsole._client_factory import storage_client_factory
    from knack.log import get_logger

    logger = get_logger(__name__)
    result = None
    storage_account_region = None
    client = _compute_client_factory(cli_ctx)
    scf = storage_client_factory(cli_ctx)

    if vmss_instanceid:
        result_data = client.virtual_machine_scale_set_vms.get_instance_view(
            resource_group_name, vm_vmss_name, vmss_instanceid)
        result = result_data

        if result_data.boot_diagnostics is None:
            error_message = "Azure Serial Console requires boot diagnostics to be enabled."
            recommendation = ('Use "az vmss update --name MyScaleSet --resource-group MyResourceGroup --set '
                              'virtualMachineProfile.diagnosticsProfile="{\\"bootDiagnostics\\": {\\"Enabled\\" : '
                              '\\"True\\",\\"StorageUri\\" : null}}"" to enable boot diagnostics. '
                              'You can replace "null" with a custom storage account '
                              '\\"https://mystor.blob.windows.net/"\\. Then run "az vmss update-instances -n '
                              'MyScaleSet -g MyResourceGroup --instance-ids *".')
            raise AzureConnectionError(
                error_message, recommendation=recommendation)
        if result.boot_diagnostics is not None:
            logger.debug(result.boot_diagnostics)
            if result.boot_diagnostics.console_screenshot_blob_uri is not None:
                storage_account_url = result.boot_diagnostics.console_screenshot_blob_uri
                storage_account_region = get_storage_account_info(storage_account_url, scf)
    else:
        try:
            result_data = client.virtual_machines.get(
                resource_group_name, vm_vmss_name, expand='instanceView')
            result = result_data
        except ComputeClientResourceNotFoundError as e:
            try:
                client.virtual_machine_scale_sets.get(resource_group_name, vm_vmss_name)
            except ComputeClientResourceNotFoundError:
                raise e from e
            error_message = e.message
            recommendation = ("We found that you specified a Virtual Machine Scale Set and not a VM. "
                              "Use the --instance-id parameter to select the VMSS instance you want to connect to.")
            raise ResourceNotFoundError(
                error_message, recommendation=recommendation) from e

        if (result.diagnostics_profile is None or
                result.diagnostics_profile.boot_diagnostics is None or
                not result.diagnostics_profile.boot_diagnostics.enabled):
            error_message = "Azure Serial Console requires boot diagnostics to be enabled."
            recommendation = ('Use "az vm boot-diagnostics enable --name MyVM --resource-group MyResourceGroup" '
                              'to enable boot diagnostics. You can specify a custom storage account with the '
                              'parameter "--storage https://mystor.blob.windows.net/".')
            raise AzureConnectionError(
                error_message, recommendation=recommendation)
        if result.diagnostics_profile is not None:
            if result.diagnostics_profile.boot_diagnostics is not None:
                storage_account_url = result.diagnostics_profile.boot_diagnostics.storage_uri
                storage_account_region = get_storage_account_info(storage_account_url, scf)

    return result, storage_account_region


def get_storage_account_info(storage_account_url, scf):
    from azext_serialconsole._arm_endpoints import ArmEndpoints

    if storage_account_url is not None:
        storage_account, storage_account_resource_group = parse_storage_account_url(storage_account_url, scf)
        if storage_account is not None and storage_account_resource_group is not None:
            sa_result = scf.storage_accounts.get_properties(storage_account_resource_group, storage_account)
            if (sa_result is not None and
                    sa_result.network_rule_set is not None and
                    len(sa_result.network_rule_set.ip_rules) > 0):
                return ArmEndpoints.region_prefix_pairings[sa_result.location]
    return None


def parse_storage_account_url(url, scf):
    if url is not None:
        sa_list = url.split('.')
        if len(sa_list) > 0:
            sa_url = sa_list[0]
            sa_name = sa_url.replace("https://", "")
            sa_resource_group = resource_group_from_storage_account_name(sa_name, scf)
            return sa_name, sa_resource_group
    return None, None


def resource_group_from_storage_account_name(storage_account_name, scf):
    storage_accounts = scf.storage_accounts.list()
    for storage_account in storage_accounts:
        storage_account_id = storage_account.id
        if storage_account_id.endswith("Microsoft.Storage/storageAccounts/" + storage_account_name):
            rg = re.search(r"resourceGroups/(.+)/providers/Microsoft.Storage/storageAccounts",
                           storage_account_id).group(1)
            return rg
    return None
