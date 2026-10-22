#!/usr/bin/env python3
"""
demo_interactive.py -- capture a real, complete conversation between
client.py and server.py, exactly as both terminals would show it.

Two terminals side by side are hard to demonstrate in a report, so this script
starts the real server.py as a child process and runs the real client.py with a
scripted stdin (three messages followed by /quit). Everything printed below is
the programs' own terminal output, not a mock-up.

It runs the conversation twice, which shows both connection strategies:

  Phase A  server.py (default: 1 message per connection, as Task 1 asks)
           -> the client transparently reconnects for messages 2 and 3.

  Phase B  server.py --messages 0 (keep the connection open)
           -> all three messages travel over ONE connection.

Run it
------
    python demo_interactive.py
"""

import pathlib
import socket
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parent
SERVER = ROOT / "server.py"
CLIENT = ROOT / "client.py"
SERVER_LOG = ROOT / "server_log.txt"
ENCODING = "utf-8"

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding=ENCODING, errors="replace")

MESSAGES = [
    "Halo server, ini pesan pertama dari client.",
    "Pesan kedua: uji komunikasi dua arah.",
    "Terakhir, pesan dengan emoji \U0001F680 dan aksen \u00e9\u00e8\u00ea",
]


def free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def wait_until_listening(port: int, limit: float = 10.0) -> None:
    deadline = time.time() + limit
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"server never listened on 127.0.0.1:{port}")


def run_session(title: str, server_args: list, log_name: str) -> None:
    """Start the server, drive the real client through it, show both terminals."""
    port = free_port()
    server_log = ROOT / log_name
    cmd = f"python server.py --port {port}"
    if server_args:
        cmd += " " + " ".join(server_args)

    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)
    print(f"  TERMINAL 1  $  {cmd}")
    print(f"  TERMINAL 2  $  python client.py --port {port}")
    print("=" * 72)

    with open(server_log, "w", encoding=ENCODING) as log_file:
        server = subprocess.Popen(
            [sys.executable, str(SERVER), "--host", "127.0.0.1",
             "--port", str(port)] + server_args,
            stdout=log_file, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
        )
        try:
            wait_until_listening(port)
            typed = "\n".join(MESSAGES + ["/quit"]) + "\n"
            client = subprocess.run(
                [sys.executable, str(CLIENT), "--host", "127.0.0.1",
                 "--port", str(port)],
                input=typed, text=True, encoding=ENCODING, errors="replace",
                stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=60,
            )
            print("\n--- TERMINAL 2 (client) ---")
            print(client.stdout.rstrip())
        finally:
            server.terminate()
            try:
                server.wait(timeout=5)
            except subprocess.TimeoutExpired:
                server.kill()

    print("\n--- TERMINAL 1 (server, what it printed meanwhile) ---")
    print(server_log.read_text(encoding=ENCODING, errors="replace").rstrip())


def main() -> int:
    run_session("PHASE A -- default server: 1 message per connection "
                "(the client reconnects)",
                [], "server_log.txt")
    run_session("PHASE B -- server --messages 0: one connection stays open "
                "for all 3 messages",
                ["--messages", "0"], "server_log_keepalive.txt")
    print()
    print("=" * 72)
    print("  Done. Both phases prove: the client can send message after "
          "message in a loop.")
    print("  Logs: server_log.txt, server_log_keepalive.txt")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    sys.exit(main())
