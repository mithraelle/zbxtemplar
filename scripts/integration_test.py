"""
Integration test: generate sample artifacts, apply to a clean Zabbix instance.

Usage:
    python scripts/integration_test.py [--no-docker] [--keep]

Requires: Docker with Compose v2 plugin, zbxtemplar and zbxtemplar-exec installed.
Generated artifacts are written to examples/ and referenced by examples/sample_scroll.yml.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = Path(__file__).resolve().parent
EXAMPLES = ROOT / "examples"
COMPOSE = SCRIPTS / "docker-compose.test.yml"
COMPOSE_PROJECT = "zbxtemplar-test"
SCROLL = EXAMPLES / "sample_scroll.yml"
ZBX_URL = f"http://127.0.0.1:{os.environ.get('ZBX_TEST_HTTP_PORT', '8888')}"

os.environ.setdefault("ZBX_ADMIN_PASSWORD", "TestSuper1234!")
os.environ.setdefault("ZBX_SERVICE_PASSWORD", "TestService1234!")
os.environ.setdefault("ZBX_ENCRYPTED_PSK", "0123456789abcdef" * 4)
os.environ.setdefault("ZBX_DB_PASSWORD", "TestMySQL1234!")


def run(*cmd, label=None):
    if label:
        print(f"\n=== {label} ===")
    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"FAILED: {' '.join(str(c) for c in cmd)}", file=sys.stderr)
        sys.exit(result.returncode)


def generate():
    run("zbxtemplar", str(EXAMPLES / "make_template.py"),
        "-o", str(EXAMPLES / "sample_combined.yml"),
        "--templates-output", str(EXAMPLES / "sample_templates.yml"),
        "--hosts-output", str(EXAMPLES / "sample_hosts.yml"),
        "--macros-output", str(EXAMPLES / "sample_global_macro.yml"),
        label="Generate template + hosts")
    run("zbxtemplar", str(EXAMPLES / "make_decree.py"),
        "--param", "admin_slack=#ops-alerts",
        "--context", str(EXAMPLES / "sample_global_macro.yml"),
        "--context", str(EXAMPLES / "sample_templates.yml"),
        "--context", str(EXAMPLES / "sample_hosts.yml"),
        "-o", str(EXAMPLES / "sample_decree.yml"),
        "--user-groups-output", str(EXAMPLES / "sample_user_group.yml"),
        "--users-output", str(EXAMPLES / "sample_set_user.yml"),
        "--actions-output", str(EXAMPLES / "sample_actions_decree.yml"),
        "--encryption-output", str(EXAMPLES / "sample_encryption_decree.yml"),
        "--saml-output", str(EXAMPLES / "sample_saml_config.yml"),
        label="Generate decree")


def docker_up():
    docker_down()
    run("docker", "compose", "-f", str(COMPOSE), "-p", COMPOSE_PROJECT, "up", "-d", "--wait",
        label="Docker up")


def wait_zabbix(timeout=120):
    print("\n=== Wait for Zabbix API ===")
    deadline = time.monotonic() + timeout
    payload = json.dumps({
        "jsonrpc": "2.0",
        "method": "user.login",
        "params": {"username": "Admin", "password": "zabbix"},
        "id": 1,
    }).encode()
    api_url = f"{ZBX_URL}/api_jsonrpc.php"
    last_error = None

    while time.monotonic() < deadline:
        try:
            request = urllib.request.Request(
                api_url,
                data=payload,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=5) as response:
                data = json.load(response)
            if data.get("result"):
                print("Zabbix API is ready")
                return
            last_error = data.get("error", data)
        except (OSError, urllib.error.URLError, json.JSONDecodeError) as exc:
            last_error = exc
        time.sleep(5)

    print(f"FAILED: Zabbix API did not become ready at {api_url}: {last_error}", file=sys.stderr)
    sys.exit(1)


def apply():
    shutil.rmtree(EXAMPLES / ".secrets", ignore_errors=True)
    run("zbxtemplar-exec", "apply", str(SCROLL),
        "--url", ZBX_URL, "--user", "Admin", "--password", "zabbix",
        label="Apply scroll")


def docker_down():
    print("\n=== Docker down ===")
    subprocess.run(["docker", "compose", "-f", str(COMPOSE), "-p", COMPOSE_PROJECT, "down"])


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-docker", action="store_true",
                        help="Generate only, skip Docker steps")
    parser.add_argument("--down", action="store_true",
                        help="Tear down the test environment and exit")
    parser.add_argument("--keep", action="store_true",
                        help="Keep the test environment running after execution")
    args = parser.parse_args()

    if args.down:
        docker_down()
        return

    generate()
    if not args.no_docker:
        try:
            docker_up()
            wait_zabbix()
            apply()
        finally:
            if not args.keep:
                docker_down()


if __name__ == "__main__":
    main()
