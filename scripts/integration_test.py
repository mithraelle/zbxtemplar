"""
Integration test: generate sample artifacts, apply to a clean Zabbix instance.

Usage:
    python scripts/integration_test.py [--no-docker]

Requires: Docker with Compose v2 plugin, zbxtemplar and zbxtemplar-exec installed.
Generated artifacts are written to examples/ and referenced by examples/sample_scroll.yml.
"""
import argparse
import os
import shutil
import subprocess
import sys
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
        label="Generate template + hosts")
    run("zbxtemplar", str(EXAMPLES / "make_decree.py"),
        "--context", str(EXAMPLES / "sample_templates.yml"),
        "--context", str(EXAMPLES / "sample_hosts.yml"),
        "-o", str(EXAMPLES / "sample_decree.yml"),
        "--user-groups-output", str(EXAMPLES / "sample_user_group.yml"),
        "--users-output", str(EXAMPLES / "sample_set_user.yml"),
        "--actions-output", str(EXAMPLES / "sample_actions_decree.yml"),
        "--encryption-output", str(EXAMPLES / "sample_encryption_decree.yml"),
        label="Generate decree")


def docker_up():
    docker_down()
    run("docker", "compose", "-f", str(COMPOSE), "-p", COMPOSE_PROJECT, "up", "-d", "--wait",
        label="Docker up")


def apply():
    shutil.rmtree(EXAMPLES / ".secrets", ignore_errors=True)
    run("zbxtemplar-exec", "scroll", str(SCROLL),
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
    args = parser.parse_args()

    if args.down:
        docker_down()
        return

    generate()
    if not args.no_docker:
        docker_up()
        apply()


if __name__ == "__main__":
    main()