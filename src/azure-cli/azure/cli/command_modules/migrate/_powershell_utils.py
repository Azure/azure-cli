# --------------------------------------------------------------------------------------------
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License. See License.txt in the project root for license information.
# --------------------------------------------------------------------------------------------

from azure.cli.core.util import run_cmd
import platform
from knack.util import CLIError
from knack.log import get_logger
import select
import sys
import threading
import queue
import time
import subprocess

logger = get_logger(__name__)


class PowerShellExecutor:
    """Cross-platform PowerShell command executor for migration operations."""
    
    def __init__(self):
        self.platform = platform.system().lower()
        try:
            self.powershell_cmd = self._get_powershell_command()
        except CLIError:
            self.powershell_cmd = None
    
    def _get_powershell_command(self):
        """Get the appropriate PowerShell command for the current platform."""
        
        if self.platform == 'windows':
            for cmd in ['powershell.exe', 'powershell']:
                try:
                    result = run_cmd([cmd, '-Command', '$PSVersionTable.PSVersion.ToString()'], 
                                    capture_output=True, timeout=10)
                    if result.returncode == 0:
                        stdout_str = result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout
                        logger.info(f'Found Windows PowerShell: {stdout_str.strip()}')
                        return cmd
                except Exception:
                    logger.debug(f'PowerShell command {cmd} not found')
        else:
            for cmd in ['pwsh']:
                try:
                    result = run_cmd([cmd, '-Command', '$PSVersionTable.PSVersion.ToString()'], 
                                    capture_output=True, timeout=10)
                    if result.returncode == 0:
                        stdout_str = result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout
                        logger.info(f'Found PowerShell Core: {stdout_str.strip()}')
                        return cmd
                except Exception:
                    logger.debug(f'PowerShell command {cmd} not found')
        
        install_guidance = {
            'windows': 'Install PowerShell Core from https://github.com/PowerShell/PowerShell or ensure Windows PowerShell is available.',
            'linux': 'Install PowerShell Core using your package manager:\n' +
                    '  Ubuntu/Debian: sudo apt update && sudo apt install -y powershell\n' +
                    '  CentOS/RHEL: sudo yum install -y powershell\n' +
                    '  Or download from: https://github.com/PowerShell/PowerShell',
            'darwin': 'Install PowerShell Core using Homebrew:\n' +
                     '  brew install powershell\n' +
                     '  Or download from: https://github.com/PowerShell/PowerShell'
        }
        
        guidance = install_guidance.get(self.platform, install_guidance['linux'])
        raise CLIError(f'PowerShell is not available on this {self.platform} system.\n{guidance}')
    
    def check_powershell_availability(self):
        """Check if PowerShell is available and return (is_available, command)."""
        if self.powershell_cmd:
            return True, self.powershell_cmd
        else:
            return False, None
    
    def execute_script(self, script_content, parameters=None):
        """Execute a PowerShell script with optional parameters."""
        try:
            cmd = [self.powershell_cmd, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command']
            
            if parameters:
                param_string = ' '.join([f'-{k} "{v}"' for k, v in parameters.items()])
                script_with_params = f'{script_content} {param_string}'
            else:
                script_with_params = script_content
            
            cmd.append(script_with_params)
            
            logger.debug(f'Executing PowerShell command: {" ".join(cmd)}')
            
            result = run_cmd(
                cmd,
                capture_output=True,
                timeout=300
            )
            
            if result.returncode != 0:
                error_msg = f'PowerShell command failed with exit code {result.returncode}'
                if result.stderr:
                    error_msg += f': {result.stderr}'
                raise CLIError(error_msg)
            
            return {
                'stdout': result.stdout.decode('utf-8') if isinstance(result.stdout, bytes) else result.stdout,
                'stderr': result.stderr.decode('utf-8') if isinstance(result.stderr, bytes) else result.stderr,
                'returncode': result.returncode
            }
            
        except Exception as e:
            if 'timeout' in str(e).lower():
                raise CLIError('PowerShell command timed out after 5 minutes')
            raise CLIError(f'Failed to execute PowerShell command: {str(e)}')
    
    def execute_script_interactive(self, script_content):
        """Execute a PowerShell script with real-time interactive output.
        
        Note: This method uses subprocess.Popen directly for real-time output streaming,
        which is an approved exception to the CLI subprocess guidelines for interactive scenarios.
        """        
        try:
            if not self.powershell_cmd:
                raise CLIError('PowerShell not available')
            
            cmd = [self.powershell_cmd, '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', script_content]
            
            logger.debug(f'Executing interactive PowerShell command: {" ".join(cmd)}')
           
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=0,
                universal_newlines=True
            )
            
            output_lines = []
            error_lines = []
            
            if platform.system().lower() == 'windows':
                stdout_queue = queue.Queue()
                stderr_queue = queue.Queue()
                
                def read_stdout():
                    for line in iter(process.stdout.readline, ''):
                        stdout_queue.put(('stdout', line))
                    stdout_queue.put(('stdout', None))
                
                def read_stderr():
                    for line in iter(process.stderr.readline, ''):
                        stderr_queue.put(('stderr', line))
                    stderr_queue.put(('stderr', None))
                
                stdout_thread = threading.Thread(target=read_stdout)
                stderr_thread = threading.Thread(target=read_stderr)
                
                stdout_thread.daemon = True
                stderr_thread.daemon = True
                
                stdout_thread.start()
                stderr_thread.start()
                
                stdout_done = False
                stderr_done = False
                
                while not (stdout_done and stderr_done):
                    try:
                        _, line = stdout_queue.get_nowait()
                        if line is None:
                            stdout_done = True
                        else:
                            line = line.rstrip('\n\r')
                            if line:
                                output_lines.append(line)
                                print(line)
                                sys.stdout.flush()
                    except queue.Empty:
                        pass
                    
                    try:
                        _, line = stderr_queue.get_nowait()
                        if line is None:
                            stderr_done = True
                        else:
                            line = line.rstrip('\n\r')
                            if line:
                                error_lines.append(line)
                                print(f"ERROR: {line}")
                                sys.stdout.flush()
                    except queue.Empty:
                        pass
                    
                    time.sleep(0.01)
                    
                    if process.poll() is not None and stdout_queue.empty() and stderr_queue.empty():
                        break
            
            else:
                while True:
                    reads = [process.stdout.fileno(), process.stderr.fileno()]
                    ret = select.select(reads, [], [])
                    
                    for fd in ret[0]:
                        if fd == process.stdout.fileno():
                            line = process.stdout.readline()
                            if line:
                                line = line.rstrip('\n\r')
                                if line:
                                    output_lines.append(line)
                                    print(line)
                                    sys.stdout.flush()
                        elif fd == process.stderr.fileno():
                            line = process.stderr.readline()
                            if line:
                                line = line.rstrip('\n\r')
                                if line:
                                    error_lines.append(line)
                                    print(f"ERROR: {line}")
                                    sys.stdout.flush()
                    
                    if process.poll() is not None:
                        break
            
            return_code = process.wait()
            
            return {
                'stdout': '\n'.join(output_lines),
                'stderr': '\n'.join(error_lines),
                'returncode': return_code
            }
            
        except Exception as e:
            print(f"ERROR executing PowerShell: {str(e)}")
            return {
                'stdout': '',
                'stderr': str(e),
                'returncode': 1
            }
   
    def execute_azure_authenticated_script(self, script, parameters=None, subscription_id=None):
        """Execute a PowerShell script with Azure authentication."""
        
        auth_prefix = """
        try {
            $context = Get-AzContext
            if (-not $context) {
                Write-Host "No Azure context found. Please run Connect-AzAccount first."
                throw "Azure authentication required"
            }
        } catch {
            Write-Host "Azure PowerShell module not available or not authenticated."
            Write-Host "Please ensure Az.Migrate module is installed and you are authenticated."
            throw "Azure authentication required"
        }
        """
        
        if subscription_id:
            auth_prefix += f"""
        try {{
            Set-AzContext -SubscriptionId "{subscription_id}"
            Write-Host "Subscription context set to: {subscription_id}"
        }} catch {{
            Write-Host "Failed to set subscription context to: {subscription_id}"
            throw "Invalid subscription ID"
        }}
        """
        
        full_script = auth_prefix + "\n" + script
        
        return self.execute_script(full_script, parameters)
    
def get_powershell_executor():
    """Get a PowerShell executor instance."""
    return PowerShellExecutor()
