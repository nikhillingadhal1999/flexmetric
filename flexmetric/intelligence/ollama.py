import ollama
import yaml

OLLAMA_MODEL = "llama3.2"
import re

def clean_response_yaml(text):
    return re.sub(r"^```[a-zA-Z]*\n?|```$", "", text.strip(), flags=re.MULTILINE)

def generate_command_yaml(task_description: str):
    prompt = f"""
You are a Prometheus expert and YAML generator for Prometheus-compatible metrics configuration.

Your task is to convert a vague user request into a valid YAML block that defines one or more shell commands for monitoring on Linux or macOS.

Follow these steps carefully:

1. Understand the user's monitoring goal from the task description.
2. Choose the most appropriate and reliable shell command that returns data relevant to the goal.
3. Mentally simulate or recall the typical output of the command and select the right indexes for label columns and value column.
4. From the output, determine:
   - Which column (if any) contains a **numeric value** suitable for `value_column`
   - Which column(s), if any, can be used as meaningful text-based Prometheus `labels`
5. Ensure the command will execute successfully on standard Linux/macOS environments and reliably return output with a numeric value.

I will repeat the above steps 5 times till I get the correct result.

🧠 Before generating YAML, apply this validation checklist:
- ✅ Are `labels` and `label_columns` both empty or both present with equal length?
- ✅ Does `value_column` point to a column containing a numeric value?
- ❌ If these conditions are not met, do not output YAML.
- ✅ Use the clean YAML format exactly as shown — no Markdown, no explanation, no extra formatting.

📦 Required output format:

commands:
  - name: ...
    command: ...
    main_label: ...
    labels: [...]
    label_columns: [...]
    value_column: ...
    timeout_seconds: ...

📘 Use this canonical example for formatting reference:

commands:
  - name: disk_usage
    command: df -h
    main_label: disk_usage_filesystem_mount_point
    labels: ["filesystem", "mounted"]
    label_columns: [0, -1]
    value_column: 4
    timeout_seconds: 60

Now apply this reasoning and generate only the final YAML.

Task description: {task_description}
"""









    response = ollama.chat(
        model=OLLAMA_MODEL,
        messages=[{"role": "user", "content": prompt}]
    )

    content = response['message']['content']
    print(content)

    # Optional: validate YAML format
    # try:
    #     filtered_content = clean_response_yaml(content)
    #     parsed_yaml = yaml.safe_load(filtered_content)
    #     if not isinstance(parsed_yaml, dict) or 'commands' not in parsed_yaml:
    #         raise ValueError("YAML structure invalid or missing 'commands'")
    # except yaml.YAMLError as e:
    #     raise RuntimeError(f"Invalid YAML returned by model: {e}")

    return content

# Example usage
if __name__ == "__main__":
    task = "Generate a command that checks disk usage and reports mounted filesystem"
    task = '''Generate a YAML command to fetch 1-minute load average using `uptime` in mac system. Use the hostname as a label, and extract the 1-minute load value. The main_label should be "load_average_1m".'''
    task = '''Generate a YAML command using `who` to count the number of logged-in users. No labels required. The main_label should be "logged_in_users".'''
    task = '''I want to monitor number of processes running under different users in my mac system '''

    yaml_block = generate_command_yaml(task)
    print(yaml_block)