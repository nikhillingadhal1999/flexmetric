#!/usr/bin/env python3
"""
Debug nested command substitution
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'flexmetric'))

from flexmetric.metric_process.process_commands import has_balanced_syntax, extract_command_substitutions, is_command_safe
from flexmetric.logging_module.logger import get_logger

logger = get_logger(__name__)

def debug_command(command):
    print(f"Debugging command: {command}")
    print(f"  has_balanced_syntax: {has_balanced_syntax(command)}")
    print(f"  extract_command_substitutions: {extract_command_substitutions(command)}")
    print(f"  is_command_safe: {is_command_safe(command)}")
    print()

if __name__ == "__main__":
    debug_command("echo $(echo $(date))")
    debug_command("echo $(date)")
    debug_command("echo `date`")
    debug_command("echo `echo \`date\``")
