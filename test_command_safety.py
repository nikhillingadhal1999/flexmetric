#!/usr/bin/env python3
"""
Test script to identify command safety issues
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'flexmetric'))

from flexmetric.metric_process.process_commands import is_command_safe
from flexmetric.logging_module.logger import get_logger

logger = get_logger(__name__)

# Test cases for safe commands that should be allowed
test_commands = [
    # Basic system commands
    "df -h",
    "uptime",
    "who",
    "ps aux",
    "free -m",
    "ls -la",
    "cat /proc/cpuinfo",
    "cat /proc/meminfo",
    "netstat -tuln",
    "ss -tuln",
    
    # Commands with pipes
    "ps aux | grep python",
    "df -h | grep -v tmpfs",
    "netstat -tuln | grep LISTEN",
    
    # Commands with output redirection (should be safe for reading)
    "cat /proc/loadavg",
    "cat /proc/stat",
    "cat /proc/version",
    
    # Commands with environment variables
    "echo $HOME",
    "echo $PATH",
    
    # Commands with command substitution (should be safe)
    "echo $(date)",
    "echo `date`",
    
    # Commands with multiple operators
    "ps aux | grep python | wc -l",
    "df -h && uptime",
    "ls -la /tmp || echo 'Directory not accessible'",
    
    # Commands with quotes
    "echo 'Hello World'",
    'echo "Hello World"',
    
    # Commands with special characters
    "find /tmp -name '*.log' -type f",
    "grep -r 'error' /var/log/",
    
    # Commands that might be problematic
    "systemctl status",  # This should be blocked
    "kill -9 1234",      # This should be blocked
    "rm -rf /tmp/test", # This should be blocked
]

def test_command_safety():
    print("Testing command safety validation...")
    print("=" * 60)
    
    safe_commands = []
    blocked_commands = []
    
    for cmd in test_commands:
        is_safe = is_command_safe(cmd)
        status = "✅ ALLOWED" if is_safe else "❌ BLOCKED"
        print(f"{status}: {cmd}")
        
        if is_safe:
            safe_commands.append(cmd)
        else:
            blocked_commands.append(cmd)
    
    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  Safe commands allowed: {len(safe_commands)}")
    print(f"  Commands blocked: {len(blocked_commands)}")
    
    print(f"\nBlocked commands that might be safe:")
    for cmd in blocked_commands:
        if cmd not in ["systemctl status", "kill -9 1234", "rm -rf /tmp/test"]:
            print(f"  - {cmd}")
    
    return safe_commands, blocked_commands

if __name__ == "__main__":
    test_command_safety()
