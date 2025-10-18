import subprocess
import yaml
import re
from flexmetric.logging_module.logger import get_logger
import re
import shlex
DANGEROUS_COMMANDS = {
    'rm', 'reboot', 'shutdown', 'halt', 'poweroff',
    'mkfs', 'dd', 'init', 'telinit', 'kill', 'killall',
    'chown', 'chmod', 'iptables', 'ufw', 'systemctl',
    'userdel', 'groupdel', 'adduser', 'addgroup',
    'yes', 'mkfs.ext4', 'mkfs.xfs', 'mkfs.ntfs',  # filesystem creation
    ':(){:|:&};:',  # fork bomb
}
SHELL_SEPARATORS = r'[;&|]{1,2}'
CMD_SUBSTITUTION_REGEX = re.compile(r'\$\((.*?)\)|`([^`]+)`', re.DOTALL)

logger = get_logger(__name__)
logger.info("prometheus is running") 

def read_commands_from_yaml(file_path):
    with open(file_path, 'r') as f:
        config = yaml.safe_load(f)
    return config.get('commands', [])

def execute_command_with_timeout(command, timeout):
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=timeout)
        if result.returncode != 0:
            logger.info(f"Exception in running the command {command}")
            return ''
        return result.stdout.strip()
    except subprocess.TimeoutExpired:
        return ''
    except Exception as ex:
        logger.error(f"Exception : {ex}")
        return ''

def parse_command_output(raw_output, label_column, value_column, fixed_label_value):
    result_list = []
    lines = raw_output.strip().splitlines()

    for line in lines:
        parts = line.strip().split()
        if not parts:
            continue

        if label_column == 'fixed':
            label = fixed_label_value or 'label'
        else:
            try:
                label = parts[label_column]
            except IndexError:
                label = 'unknown'

        try:
            raw_value = parts[value_column]
            cleaned_value = re.sub(r'[^\d\.\-]', '', raw_value)
            value = float(cleaned_value) if cleaned_value else 1
        except (IndexError, ValueError):
            value = 1

        result_list.append({'label': label, 'value': value})

    return result_list

def process_single_command(cmd_info):
    command = cmd_info['command']
    timeout = cmd_info.get('timeout_seconds', 30)
    labels = cmd_info.get('labels', [])
    label_columns = cmd_info.get('label_columns', [])
    value_column = cmd_info.get('value_column', 0)
    main_label = cmd_info.get('main_label', 'default_metric')

    raw_output = execute_command_with_timeout(command, timeout)
    if not raw_output:
        logger.warning(f"No results for command {command}")
        return None

    lines = raw_output.strip().split('\n')
    if not lines:
        logger.error(f"No valid lines returned from command: {command}")
        return None
    result_list = []
    for line in lines:
        parts = line.split()
        try:
            label_columns_value = []
            for value in label_columns:
                label_columns_value.append(parts[value])
            result_list.append({ "label": label_columns_value, "value": parts[value_column] })
        except Exception as e:
            logger.error(f"Error parsing line: '{line}' → {e}")
            continue
    return {
        'result': result_list,
        'labels': labels,
        'main_label': main_label
    }



def extract_subcommands(command):
    return [cmd.strip() for cmd in re.split(SHELL_SEPARATORS, command) if cmd.strip()]

def contains_dangerous_token(tokens):
    if not tokens:
        return False
    
    # Only check the first token (command name), not arguments
    first_token = tokens[0].lower()
    return first_token in DANGEROUS_COMMANDS

def is_basic_command_safe(command):
    """Basic safety check for command substitutions - more lenient than full safety check"""
    if not command.strip():
        return True
    
    # Split the command and check only the first token
    tokens = command.split()
    if not tokens:
        return True
    
    first_token = tokens[0].lower()
    return first_token not in DANGEROUS_COMMANDS

def has_balanced_syntax(command: str) -> bool:
    stack = []
    i = 0
    while i < len(command):
        if command[i:i+2] == '$(':
            stack.append('$(')
            i += 2
        elif command[i] == '(' and stack and stack[-1] == '$(':
            stack.append('(')
            i += 1
        elif command[i] == ')' and stack:
            # Pop until we find the matching $(
            while stack:
                top = stack.pop()
                if top == '$(':
                    break
            i += 1
        else:
            i += 1
    
    # Check for unmatched $(
    if any(item == '$(' for item in stack):
        return False

    # Check for unmatched backticks (handle escaped backticks)
    backtick_count = 0
    i = 0
    while i < len(command):
        if command[i] == '`':
            if i == 0 or command[i-1] != '\\':
                backtick_count += 1
        i += 1
    
    if backtick_count % 2 != 0:
        return False

    return True

def has_invalid_operator_usage(command: str) -> bool:
    # Handle special cases like find -exec commands
    if 'find' in command and '-exec' in command:
        return False
    
    # Handle commands with escaped characters that might be misinterpreted
    if '\\' in command and ('find' in command or 'grep' in command):
        return False
    
    tokens = re.split(r'([;&|]{1,2})', command)
    tokens = [t.strip() for t in tokens if t.strip() != '']

    last_was_operator = True

    for token in tokens:
        if re.fullmatch(r'[;&|]{1,2}', token):
            if last_was_operator:
                return True
            last_was_operator = True
        else:
            last_was_operator = False

    return last_was_operator

def extract_command_substitutions(command: str):
    subs = []
    stack = []
    i = 0
    while i < len(command):
        if command[i:i+2] == '$(':
            stack.append(i)
            i += 2
        elif command[i] == ')' and stack:
            start = stack.pop()
            subs.append(command[start+2:i])
            i += 1
        elif command[i] == '`':
            # Handle escaped backticks
            if i > 0 and command[i-1] == '\\':
                i += 1
                continue
            # Find matching backtick, handling nested cases
            end = i + 1
            while end < len(command):
                if command[end] == '`' and (end == 0 or command[end-1] != '\\'):
                    break
                end += 1
            if end < len(command):
                subs.append(command[i+1:end])
                i = end + 1
            else:
                return None
        else:
            i += 1

    if stack:
        return None 
    return subs


def is_command_safe(command):
    if not command.strip():
        return True
    
    # Special check for fork bomb
    if ':(){:|:&};:' in command:
        logger.warning(f"Fork bomb detected in command: {command}")
        return False
    
    if not has_balanced_syntax(command=command):
        logger.warning(f"Unbalanced syntax detected in command: {command}")
        return False
    substitutions = extract_command_substitutions(command)
    if substitutions is None:
        logger.warning(f"Malformed command detected: {command}")
        return False

    for sub in substitutions:
        # For substitutions, we need to be more lenient - only check for truly dangerous commands
        if sub.strip() and not is_basic_command_safe(sub):
            logger.warning(f"Dangerous command detected in substitution: {sub}")
            return False
    
    if has_invalid_operator_usage(command=command):
        logger.warning(f"Invalid operator usage detected in command: {command}")
        return False
    for match in CMD_SUBSTITUTION_REGEX.finditer(command):
        inner_cmd = match.group(1) or match.group(2)
        if not is_basic_command_safe(inner_cmd):
            logger.warning(f"Dangerous command detected in substitution: {inner_cmd}")
            return False

    subcommands = extract_subcommands(command)

    for subcmd in subcommands:
        try:
            # Handle commands with escaped characters more gracefully
            if '\\' in subcmd:
                # For commands with backslashes, use a more lenient parsing
                tokens = subcmd.split()
            else:
                tokens = shlex.split(subcmd, posix=True)
        except ValueError:
            # If shlex fails, try basic splitting as fallback
            tokens = subcmd.split()
            if not tokens:
                logger.error(f"Malformed command: {subcmd}")
                return False

        if contains_dangerous_token(tokens):
            logger.warning(f"Dangerous command detected: {subcmd}")
            return False

    return True

def process_commands(config_file):
    commands = read_commands_from_yaml(config_file)
    all_results = []

    for cmd_info in commands:
        command = cmd_info.get('command', '')
        if not command:
            logger.error("Command is missing in the configuration.")
            continue

        if not is_command_safe(command):
            logger.warning(f"Command '{command}' is not allowed and will not be executed.")
            continue

        try:
            formatted_result = process_single_command(cmd_info)
            if formatted_result:
                all_results.append(formatted_result)
        except KeyError as e:
            logger.error(f"Missing key in command configuration: {e}. Command: {cmd_info}")
        except Exception as e:
            logger.error(f"An error occurred while processing command '{command}': {e}")

    return all_results

# # Example usage:
# if __name__ == "__main__":
#     results = process_commands('/Users/nlingadh/code/custom_prometheus_agent/src/commands.yaml')
#     print(results)
