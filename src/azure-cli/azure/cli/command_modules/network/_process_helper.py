# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

# pylint: disable=too-few-public-methods

import subprocess
from ctypes import WinDLL, c_int, c_size_t, Structure, WinError, sizeof, pointer
from ctypes.wintypes import BOOL, DWORD, HANDLE, LPVOID, LPCWSTR, LPDWORD
from knack.log import get_logger

logger = get_logger(__name__)


def _errcheck(is_error_result=(lambda result: not result)):
    def impl(result, func, args):
        # pylint: disable=unused-argument
        if is_error_result(result):
            raise WinError()

        return result

    return impl


# Win32 CreateJobObject
kernel32 = WinDLL("kernel32")
kernel32.CreateJobObjectW.errcheck = _errcheck(lambda result: result == 0)
kernel32.CreateJobObjectW.argtypes = (LPVOID, LPCWSTR)
kernel32.CreateJobObjectW.restype = HANDLE


# Win32 OpenProcess
PROCESS_TERMINATE = 0x0001
PROCESS_SET_QUOTA = 0x0100
PROCESS_SYNCHRONIZE = 0x00100000
kernel32.OpenProcess.errcheck = _errcheck(lambda result: result == 0)
kernel32.OpenProcess.restype = HANDLE
kernel32.OpenProcess.argtypes = (DWORD, BOOL, DWORD)

# Win32 WaitForSingleObject
INFINITE = 0xFFFFFFFF
# kernel32.WaitForSingleObject.errcheck = _errcheck()
kernel32.WaitForSingleObject.argtypes = (HANDLE, DWORD)
kernel32.WaitForSingleObject.restype = DWORD

# Win32 AssignProcessToJobObject
kernel32.AssignProcessToJobObject.errcheck = _errcheck()
kernel32.AssignProcessToJobObject.argtypes = (HANDLE, HANDLE)
kernel32.AssignProcessToJobObject.restype = BOOL

# Win32 QueryInformationJobObject
JOBOBJECTCLASS = c_int
JobObjectBasicProcessIdList = JOBOBJECTCLASS(3)


class JOBOBJECT_BASIC_PROCESS_ID_LIST(Structure):
    _fields_ = [('NumberOfAssignedProcess', DWORD),
                ('NumberOfProcessIdsInList', DWORD),
                ('ProcessIdList', c_size_t * 1)]


kernel32.QueryInformationJobObject.errcheck = _errcheck()
kernel32.QueryInformationJobObject.restype = BOOL
kernel32.QueryInformationJobObject.argtypes = (HANDLE, JOBOBJECTCLASS, LPVOID, DWORD, LPDWORD)


def launch_and_wait(command):
    """Windows Only: Runs and waits for the command to exit. It creates a new process and
    associates it with a job object. It then waits for all the job object child processes
    to exit.
    """
    try:
        job = kernel32.CreateJobObjectW(None, None)
        process = subprocess.Popen(command)

        # Terminate and set quota are required to join process to job
        process_handle = kernel32.OpenProcess(
            PROCESS_TERMINATE | PROCESS_SET_QUOTA,
            False,
            process.pid,
        )
        kernel32.AssignProcessToJobObject(job, process_handle)

        job_info = JOBOBJECT_BASIC_PROCESS_ID_LIST()
        job_info_size = DWORD(sizeof(job_info))

        while True:
            kernel32.QueryInformationJobObject(
                job,
                JobObjectBasicProcessIdList,
                pointer(job_info),
                job_info_size,
                pointer(job_info_size))

            # Wait for the first running child under the job object
            if job_info.NumberOfProcessIdsInList > 0:
                logger.debug("Waiting for process %d", job_info.ProcessIdList[0])
                # Synchronize access is required to wait on handle
                child_handle = kernel32.OpenProcess(
                    PROCESS_SYNCHRONIZE,
                    False,
                    job_info.ProcessIdList[0],
                )
                kernel32.WaitForSingleObject(child_handle, INFINITE)
            else:
                break

    except OSError as e:
        logger.error("Could not run '%s' command. Exception: %s", command, str(e))
