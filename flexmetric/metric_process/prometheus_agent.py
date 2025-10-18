from prometheus_client import Gauge, start_http_server
import psutil
import time
import sys
import os
from flexmetric.config.configuration import CA_PATH, CERT_PATH, KEY_PATH
from flexmetric.logging_module.logger import get_logger
from flexmetric.file_recognition.exec_file import execute_functions
from flexmetric.metric_process.process_commands import process_commands
from flexmetric.metric_process.database_processing import process_database_queries
from flexmetric.metric_process.expiring_queue import metric_queue
import argparse
import os
from flexmetric.metric_process.views import (
    run_flask,
    add_update_metric_route,
    secure_flask_run,
)
import sched
import threading

scheduler = sched.scheduler(time.time, time.sleep)


def arguments():
    parser = argparse.ArgumentParser(
        description="FlexMetric: A flexible Prometheus exporter for commands, databases, scripts, and Python functions."
    )

    # Input type flags
    parser.add_argument(
        "--database",
        action="store_true",
        help="Process database.yaml and queries.yaml to extract metrics from databases.",
    )
    parser.add_argument(
        "--commands",
        action="store_true",
        help="Process commands.yaml to extract metrics from system commands.",
    )
    parser.add_argument(
        "--functions",
        action="store_true",
        help="Process Python functions from the provided path to extract metrics.",
    )
    parser.add_argument(
        "--expose-api",
        action="store_true",
        help="Expose Flask API to receive external metric updates.",
    )

    # Config file paths
    parser.add_argument(
        "--database-config",
        type=str,
        default=None,
        help="Path to the database configuration YAML file.",
    )
    parser.add_argument(
        "--queries-config",
        type=str,
        default=None,
        help="Path to the database queries YAML file.",
    )
    parser.add_argument(
        "--commands-config",
        type=str,
        default=None,
        help="Path to the commands configuration YAML file.",
    )
    parser.add_argument(
        "--functions-dir", type=str, default=None, help="Path to the python files dir."
    )
    parser.add_argument(
        "--functions-file",
        type=str,
        default=None,
        help="Path to the file containing which function to execute",
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="port on which exportor runs"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="The hostname or IP address on which to run the Flask server (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--enable-https",
        action="store_true",
        help="Enable HTTPS for Flask API using SSL certificates.",
    )
    parser.add_argument(
        "--ssl-cert",
        type=str,
        help="Path to the SSL certificate file (cert.pem) for HTTPS.",
    )
    parser.add_argument(
        "--ssl-key",
        type=str,
        help="Path to the SSL private key file (key.pem) for HTTPS.",
    )

    return parser.parse_args()


logger = get_logger(__name__)

logger.info("prometheus is running")


def convert_to_data_type(value):
    if isinstance(value, str) and "%" in value:
        return float(value.strip("%"))
    elif isinstance(value, str) and ("GB" in value or "MB" in value):
        return float(value.split()[0].replace(",", ""))
    return value


gauges = {}


def validate_required_files(mode_name, required_files):
    missing = [desc for desc, path in required_files.items() if path == None]
    if missing:
        logger.error(
            f"Missing {', '.join(missing)} for '{mode_name}' mode. Skipping..."
        )
        return False

    return True


def validate_all_modes(args):
    """
    Validates all selected modes and their required files.

    Args:
        args: Parsed command-line arguments.

    Returns:
        bool: True if at least one valid mode is properly configured, False otherwise.
    """
    has_valid_mode = False

    mode_validations = [
        (
            args.database,
            "database",
            {
                "database-config": args.database_config,
                "queries-config": args.queries_config,
            },
        ),
        (args.commands, "commands", {"commands-config": args.commands_config}),
        (
            args.functions,
            "functions",
            {
                "functions-dir": args.functions_dir,
                "functions-file": args.functions_file,
            },
        ),
        (args.expose_api, "expose-api", {}),
        (args.enable_https,"enable-https",{"ssl-cert":args.ssl_cert,"ssl-key" :args.ssl_key})
    ]

    for is_enabled, mode_name, files in mode_validations:
        if is_enabled:
            if validate_required_files(mode_name, files):
                has_valid_mode = True

    return has_valid_mode


def measure(args):
    exec_result = []
    queue_items = metric_queue.pop_all()
    if len(queue_items) != 0:
        exec_result.extend(queue_items)
    if args.database:
        db_results = process_database_queries(args.queries_config, args.database_config)
        exec_result.extend(db_results)
    if args.functions:
        function_results = execute_functions(args.functions_dir, args.functions_file)
        exec_result.extend(function_results)
    if args.commands:
        cmd_results = process_commands(args.commands_config)
        if cmd_results != None:
            exec_result.extend(cmd_results)
    global gauges

    for data in exec_result:
        results = data["result"]
        labels = data["labels"]
        main_label_value = data.get("main_label", "default_main")
        gauge_name = main_label_value.lower() + "_gauge"

        if gauge_name not in gauges:
            gauge = Gauge(gauge_name, f"{gauge_name} for different metrics", labels)
            gauges[gauge_name] = gauge
        else:
            gauge = gauges[gauge_name]

        for result in results:
            label_values = result["label"]

            if not isinstance(label_values, list):
                # Automatically wrap single label into list for consistency
                label_values = [label_values]

            if len(label_values) != len(labels):
                logger.error(f"Label mismatch: expected {len(labels)} values but got {len(label_values)}")
                continue

            label_dict = dict(zip(labels, label_values))
            # print(label_dict)

            try:
                if len(label_dict) > 0:
                    gauge.labels(**label_dict).set(convert_to_data_type(result["value"]))
                else:
                    gauge.set(result["value"])
            except Exception as ex:
                logger.error(f"Failed to set gauge for labels {label_dict}: {ex}")


def scheduled_measure(args):
    measure(args)
    scheduler.enter(5, 1, scheduled_measure, (args,))


def start_scheduler(args):
    scheduler.enter(0, 1, scheduled_measure, (args,))
    scheduler.run()


def main():
    args = arguments()
    logger.info("Validating configuration...")
    if not validate_all_modes(args):
        logger.error("No valid modes with proper configuration found. Exiting.")
        exit(1)

    logger.info(f"Starting Prometheus metrics server on port {args.port}...")
    logger.info("Starting server")
    # start_http_server(args.port)

    scheduler_thread = threading.Thread(
        target=start_scheduler, args=(args,), daemon=True
    )
    scheduler_thread.start()
    if args.expose_api:
        add_update_metric_route()
    if args.enable_https:
        secure_flask_run(args)
    else:
        run_flask(args.host, args.port)
# # args = arguments()
# # measure(args)
main()