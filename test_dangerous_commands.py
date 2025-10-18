#!/usr/bin/env python3
"""
Test that dangerous commands are still properly blocked
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'flexmetric'))

from flexmetric.metric_process.process_commands import is_command_safe
from flexmetric.logging_module.logger import get_logger

logger = get_logger(__name__)

# Commands that should be blocked
dangerous_commands = [
    "rm -rf /",
    "rm -rf /tmp/test",
    "systemctl stop nginx",
    "systemctl status",
    "kill -9 1234",
    "killall python",
    "reboot",
    "shutdown -h now",
    "halt",
    "poweroff",
    "chmod 777 /etc/passwd",
    "chown root:root /etc/passwd",
    "userdel testuser",
    "groupdel testgroup",
    "adduser testuser",
    "iptables -F",
    "ufw disable",
    "dd if=/dev/zero of=/dev/sda",
    "mkfs.ext4 /dev/sda1",
    "init 0",
    "telinit 0",
    "yes",
    ":(){:|:&};:",  # fork bomb
]

def test_dangerous_commands():
    print("Testing that dangerous commands are properly blocked...")
    print("=" * 60)
    
    blocked_count = 0
    allowed_count = 0
    
    for cmd in dangerous_commands:
        is_safe = is_command_safe(cmd)
        status = "❌ BLOCKED" if not is_safe else "✅ ALLOWED"
        print(f"{status}: {cmd}")
        
        if is_safe:
            allowed_count += 1
        else:
            blocked_count += 1
    
    print("\n" + "=" * 60)
    print(f"Summary:")
    print(f"  Dangerous commands blocked: {blocked_count}")
    print(f"  Dangerous commands allowed: {allowed_count}")
    
    if allowed_count > 0:
        print(f"\n⚠️  WARNING: {allowed_count} dangerous commands were allowed!")
        return False
    else:
        print(f"\n✅ SUCCESS: All dangerous commands were properly blocked!")
        return True

if __name__ == "__main__":
    success = test_dangerous_commands()
    exit(0 if success else 1)
