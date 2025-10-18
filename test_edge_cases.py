#!/usr/bin/env python3
"""
Test edge cases for command safety
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'flexmetric'))

from flexmetric.metric_process.process_commands import is_command_safe
from flexmetric.logging_module.logger import get_logger

logger = get_logger(__name__)

# Edge cases that might cause issues
edge_case_commands = [
    # Commands with complex quoting
    'echo "Hello World"',
    "echo 'Hello World'",
    'echo "It\'s a test"',
    "echo 'It\"s a test'",
    
    # Commands with nested substitutions
    "echo $(echo $(date))",
    "echo `echo \`date\``",
    
    # Commands with special shell characters
    "ps aux | grep -v grep | wc -l",
    "df -h | awk '{print $5}' | sed 's/%//'",
    
    # Commands with environment variables and substitutions
    "echo $HOME/$(date +%Y)",
    "ls -la $HOME/`date +%Y`",
    
    # Commands that might be misidentified as dangerous
    "ps aux | grep -v systemctl",
    "grep -r 'systemctl' /var/log/",
    "find /tmp -name '*systemctl*'",
    
    # Commands with multiple operators
    "ps aux | grep python && echo 'Found python processes'",
    "df -h || echo 'df command failed'",
    "uptime; ps aux | head -5",
    
    # Commands with complex paths
    "ls -la /usr/local/bin/",
    "find /var/log -name '*.log' -exec wc -l {} \\;",
    
    # Commands that should be safe but might be blocked
    "which python3",
    "whereis python3",
    "type python3",
    "command -v python3",
    
    # Commands with arithmetic
    "echo $((1 + 1))",
    "expr 1 + 1",
    
    # Commands with test conditions
    "[ -f /etc/passwd ] && echo 'passwd exists'",
    "test -d /tmp && echo 'tmp is directory'",
]

def test_edge_cases():
    print("Testing edge cases for command safety...")
    print("=" * 60)
    
    safe_commands = []
    blocked_commands = []
    
    for cmd in edge_case_commands:
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
    
    if blocked_commands:
        print(f"\nBlocked commands:")
        for cmd in blocked_commands:
            print(f"  - {cmd}")
    
    return safe_commands, blocked_commands

if __name__ == "__main__":
    test_edge_cases()
