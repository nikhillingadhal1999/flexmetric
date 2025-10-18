# FlexMetric

[![PyPI version](https://badge.fury.io/py/flexmetric.svg)](https://badge.fury.io/py/flexmetric)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**FlexMetric** is a lightweight, pluggable, and extensible Prometheus exporter that helps you collect, expose, and visualize custom metrics with minimal setup and maximum flexibility.

## Features

- **Command Execution**: Run system commands and expose their output as Prometheus metrics
- **Database Monitoring**: Execute SQL queries against SQLite, PostgreSQL, and ClickHouse databases
- **Python Functions**: Call custom Python functions and export their results as metrics
- **REST API**: Receive externally submitted metrics via a secure Flask-based API with optional HTTPS (TLS)
- **Security First**: Built-in command and query sanitization to prevent dangerous operations
- **Prometheus Ready**: All metrics are exposed in Prometheus-compatible format for Grafana visualization

## Safety Features

- **Command Safety**: Harmful commands (file deletion, system shutdown) are automatically blocked
- **Query Protection**: Potentially dangerous SQL queries (`DROP`, `DELETE`, `TRUNCATE`) are blocked by default
- **Input Validation**: Comprehensive sanitization and validation ensure only safe operations are executed

---

## Installation

Install FlexMetric from PyPI:

```bash
pip install flexmetric
```

## Quick Start

Run FlexMetric with command execution mode:

```bash
flexmetric --commands --commands-config commands.yaml --port 8000
```

Access your metrics at: `http://localhost:8000/metrics`

## Available Modes

FlexMetric supports multiple modes that can be used individually or combined:

| Mode | Description | Configuration Files |
|------|-------------|-------------------|
| `--commands` | Execute system commands and export outputs as metrics | `commands.yaml` |
| `--database` | Execute SQL queries on databases and export results | `database.yaml`, `queries.yaml` |
| `--functions` | Discover and run user-defined Python functions | `executable_functions.txt` |
| `--expose-api` | Expose Flask API to receive external metrics | None required |

### Using Multiple Modes Together

```bash
flexmetric \
  --commands --commands-config commands.yaml \
  --database --database-config database.yaml --queries-config queries.yaml \
  --functions --functions-file executable_functions.txt \
  --expose-api --port 8000
```

## Configuration Examples

### Commands Mode

Create a `commands.yaml` file to define system commands to execute:

```yaml
commands:
  - name: disk_usage
    command: df -h
    main_label: disk_usage_filesystem_mount_point
    labels: ["filesystem", "mounted"]
    label_columns: [0, -1]
    value_column: 4
    timeout_seconds: 60
```

**Example command output:**
```bash
Filesystem      Size  Used Avail Use% Mounted on
/dev/sda1        50G   20G   28G  42% /
/dev/sdb1       100G   10G   85G  10% /data
```

#### Configuration Fields

| Field | Description |
|-------|-------------|
| `name` | A nickname for this command (e.g., `"disk_usage"`) |
| `command` | The actual shell command to run (e.g., `"df -h"`) |
| `main_label` | The metric name that will appear in Prometheus |
| `labels` | List of label names for different dimensions |
| `label_columns` | Column indexes to extract label values (e.g., `[0, -1]`) |
| `value_column` | Column index to extract the numeric value |
| `timeout_seconds` | Maximum time to wait for command completion |

### Database Mode

FlexMetric supports multiple databases with simple YAML configuration:

#### Supported Databases

| Database | Type | Description |
|----------|------|-------------|
| **SQLite** | `sqlite` | Lightweight, file-based database |
| **PostgreSQL** | `postgres` | Production-grade relational database |
| **ClickHouse** | `clickhouse` | High-performance analytical database |

#### Database Configuration (`database.yaml`)
```yaml
databases:
  - id: "local_sqlite"
    type: "sqlite"
    db_connection: "/path/to/example.db"

  - id: "analytics_pg"
    type: "postgres"
    host: "localhost"
    port: 5432
    database: "metricsdb"
    username: "postgres"
    password: "postgres_password"
    sslmode: "disable"

  - id: "clickhouse_cluster"
    type: "clickhouse"
    host: "localhost"
    port: 8443
    username: "default"
    password: "clickhouse_password"
    secure: true
```

#### Query Configuration (`queries.yaml`)

```yaml
commands:
  - id: "active_user_count_pg"
    type: "postgres"
    database_id: "analytics_pg"
    query: |
      SELECT
        country AS country_name,
        COUNT(*) AS active_user_count
      FROM users
      WHERE is_active = true
      GROUP BY country;
    main_label: "active_user_count"
    labels: ["country_name"]
    value_column: "active_user_count"
```

### Functions Mode

Create an `executable_functions.txt` file listing your Python functions:

```
function_name_1
function_name_2
```

#### Python Function Output Format

Each function should return a dictionary:

```python
{
    'result': [
        { 'label': [label_value1, label_value2, ...], 'value': numeric_value }
    ],
    'labels': [label_name1, label_name2, ...],
    'main_label': 'your_main_metric_name'
}
```

### Flask API Mode

Start FlexMetric with the Flask API:

```bash
flexmetric --expose-api --port 5000 --host 0.0.0.0
```

**Endpoints:**
- Metrics: `http://localhost:5000/metrics`
- API: `http://localhost:5000/update_metric`

#### Submit Metrics via API

```bash
curl -X POST http://localhost:5000/update_metric \
-H "Content-Type: application/json" \
-d '{
  "result": [
    { 
      "label": ["cpu", "core_1"], 
      "value": 42.5 
    }
  ],
  "labels": ["metric_type", "core"],
  "main_label": "cpu_usage_metric"
}'
```

#### Secure HTTPS Mode

```bash
flexmetric --expose-api --enable-https --ssl-cert=cert.pem --ssl-key=key.pem
```

**HTTPS Endpoints:**
- Metrics: `https://localhost:5000/metrics`
- API: `https://localhost:5000/update_metric`

#### Submit Metrics via HTTPS API

```bash
curl -k -X POST https://localhost:5000/update_metric \
-H "Content-Type: application/json" \
-d '{
  "result": [
    { 
      "label": ["cpu", "core_1"], 
      "value": 42.5 
    }
  ],
  "labels": ["metric_type", "core"],
  "main_label": "cpu_usage_metric"
}'
```

#### Python HTTPS Client Example

```python
import requests
import json
import urllib3

# Disable SSL warnings for self-signed certificates
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://localhost:5000/update_metric"
headers = {
    "Content-Type": "application/json"
}
data = {
    "result": [
        {
            "label": ["cpu", "core_1"],
            "value": 42.5
        }
    ],
    "labels": ["metric_type", "core"],
    "main_label": "cpu_usage_metric"
}

# Use verify=False for self-signed certificates (not recommended for production)
response = requests.post(url, headers=headers, data=json.dumps(data), verify=False)

print(f"Status Code: {response.status_code}")
print("Response:", response.text)
```

#### SSL Certificate Generation

For development/testing, you can generate self-signed certificates:

```bash
# Generate private key
openssl genrsa -out key.pem 2048

# Generate certificate
openssl req -new -x509 -key key.pem -out cert.pem -days 365 -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
```

**Note**: For production use, use certificates from a trusted Certificate Authority (CA).

## Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `--port` | Prometheus metrics server port | `8000` |
| `--commands` | Enable commands mode | |
| `--commands-config` | Path to commands YAML file | `commands.yaml` |
| `--database` | Enable database mode | |
| `--database-config` | Path to database YAML file | `database.yaml` |
| `--queries-config` | Path to queries YAML file | `queries.yaml` |
| `--functions` | Enable Python functions mode | |
| `--functions-file` | Path to functions file | `executable_functions.txt` |
| `--expose-api` | Enable Flask API mode | |
| `--flask-port` | Flask API port | `5000` |
| `--flask-host` | Flask API hostname | `0.0.0.0` |
| `--enable-https` | Enable HTTPS for Flask API | |
| `--ssl-cert` | SSL certificate file path | |
| `--ssl-key` | SSL private key file path | |

## Example Output

FlexMetric exposes metrics in Prometheus format:

```bash
# HELP disk_usage_gauge Disk usage percentage
# TYPE disk_usage_gauge gauge
disk_usage_gauge{filesystem="/dev/sda1",mounted="/"} 42.0
disk_usage_gauge{filesystem="/dev/sdb1",mounted="/data"} 10.0
```

## Future Enhancements

- Support for additional databases (MySQL, MongoDB)
- Enhanced label extraction and parsing
- Web UI for configuration management
- Advanced security features and authentication