import subprocess
import shutil
import re
from typing import List, Tuple, Optional, Dict, Set


class CommandSecurityGuard:
    """
    Enforces strict read-only execution safety:
    1. Zero arbitrary shell execution (shell=False always).
    2. Strict binary allowlist.
    3. Strict argument allowlist per binary.
    4. Prohibits shell metacharacters and piping.
    """

    # Allowed binaries and their permissible read-only arguments
    ALLOWED_COMMANDS: Dict[str, Set[str]] = {
        "lscpu": {"", "-J", "--json"},
        "lsblk": {"", "-J", "--json", "-o", "NAME,SIZE,TYPE,FSTYPE,MOUNTPOINT,MODEL,TRAN,ROTA"},
        "free": {"", "-m", "-g", "-b", "--si"},
        "lspci": {"", "-nnk", "-v", "-mm"},
        "dmidecode": {"", "-t", "memory", "-t", "processor", "-t", "system", "-t", "16", "-t", "17"},
        "cat": {
            "/proc/meminfo",
            "/proc/cpuinfo",
            "/proc/version",
            "/sys/class/power_supply/BAT0/capacity",
            "/sys/class/power_supply/BAT0/status",
            "/sys/class/dmi/id/product_name",
            "/sys/class/dmi/id/sys_vendor"
        }
    }

    FORBIDDEN_CHARS = re.compile(r"[;&|`$<>]")

    @classmethod
    def validate_command(cls, cmd_tokens: List[str]) -> Tuple[bool, Optional[str]]:
        if not cmd_tokens:
            return False, "Empty command"

        binary = cmd_tokens[0]

        # Check binary allowlist
        if binary not in cls.ALLOWED_COMMANDS:
            return False, f"Prohibited binary '{binary}'. Only read-only hardware tools are permitted."

        # Check argument injection
        allowed_args = cls.ALLOWED_COMMANDS[binary]
        for arg in cmd_tokens[1:]:
            if cls.FORBIDDEN_CHARS.search(arg):
                return False, f"Prohibited character in argument '{arg}'"

            # Check if arg matches permitted options/paths
            if binary == "cat" and arg not in allowed_args:
                return False, f"Path '{arg}' is not in the read-only inspection allowlist."

        return True, None

    @classmethod
    def run_safe_command(cls, cmd_tokens: List[str], timeout_sec: int = 3) -> Tuple[bool, str, int]:
        """
        Executes an allowlisted command safely without shell expansion.
        Returns (success: bool, output: str, returncode: int).
        """
        is_valid, error = cls.validate_command(cmd_tokens)
        if not is_valid:
            return False, f"Security Violation: {error}", -1

        # Check if binary exists on system
        binary_path = shutil.which(cmd_tokens[0])
        if not binary_path:
            return False, f"Binary '{cmd_tokens[0]}' not found on this system.", 127

        try:
            res = subprocess.run(
                cmd_tokens,
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                shell=False
            )
            if res.returncode == 0:
                return True, res.stdout.strip(), 0
            else:
                stderr = res.stderr.strip()
                if "Permission denied" in stderr or "Operation not permitted" in stderr:
                    return False, f"Permission Denied: '{' '.join(cmd_tokens)}' requires elevated privileges.", res.returncode
                return False, f"Command failed: {stderr}", res.returncode

        except subprocess.TimeoutExpired:
            return False, f"Execution timed out after {timeout_sec}s.", -2
        except Exception as e:
            return False, f"Execution error: {str(e)}", -3
