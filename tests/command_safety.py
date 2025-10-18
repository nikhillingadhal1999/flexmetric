import pytest
import os
import sys

root_path = os.path.abspath(os.path.dirname(".."))
    
if root_path not in sys.path:
    sys.path.insert(0, root_path)
from flexmetric.metric_process.process_commands import is_command_safe

@pytest.mark.parametrize("command", [
    "echo 'hello world'",
    "ls -la",
    "cat /etc/passwd",
    "grep 'pattern' file.txt",
    "sleep 1",
    "echo 'safe'; echo 'also safe'",
    "ls && echo 'safe'",
    "uptime || true",
    "echo `date`",
    "echo $(whoami)",
    "echo '$(ls)'",
    "",
    "   ",
])
def test_safe_commands(command):
    assert is_command_safe(command) == True

@pytest.mark.parametrize("command", [
    "rm -rf /",
    "shutdown now",
    "reboot",
    "poweroff",
    "mkfs.ext4 /dev/sda1",
    "dd if=/dev/zero of=/dev/sda",
    "init 0",
    "kill -9 1",
    "killall process",
    "userdel root",
    "chmod 777 /etc/shadow",
    "chown root:root /",
    "iptables -F",
    "ufw disable",
    ":(){ :|:& };:",
    "rm -rf /; echo 'done'",
    "sleep 1 && shutdown now",
    "yes | mkfs.ext4 /dev/sda1",
    "$(reboot)",
    "`shutdown now`",
    "echo $(rm -rf /)",
    "echo `dd if=/dev/zero of=/dev/null`",
])
def test_dangerous_commands(command):
    assert is_command_safe(command) == False

@pytest.mark.parametrize("command", [
    "echo 'safe text'; ls | grep 'py'",
    "echo safe && echo still_safe",
    "echo $(echo $(ls))",
])
def test_complex_safe_commands(command):
    assert is_command_safe(command) == True

@pytest.mark.parametrize("command", [
    "rm -rf / && echo safe",
    "echo $(rm -rf /)",
    "echo safe; shutdown now",
    "echo `poweroff`",
    "`echo $(reboot)`",
])
def test_complex_dangerous_commands(command):
    assert is_command_safe(command) == False

@pytest.mark.parametrize("command", [
    "echo 'unclosed quote",
    "ls -la | | grep x",
    "echo $(echo $(unclosed",
])
def test_malformed_commands(command):
    assert is_command_safe(command) == False
