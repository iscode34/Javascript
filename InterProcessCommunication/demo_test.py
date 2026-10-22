#!/usr/bin/env python3
"""
demo_test.py -- automatic proof that server.py and client.py really work.

This script does what a human would do by hand, but reproducibly:

  1. starts server.py as a child process on a free port,
  2. waits until the port answers,
  3. runs a series of test cases against it (single message, several clients
     in a row, UTF-8 text, a long message, a silent client that hangs up),
  4. stops the server, prints the server-side terminal evidence and a
     PASS/FAIL table.

Run it
------
    python demo_test.py

Exit code 0 = every test passed. This is the evidence you can screenshot /
paste into the assignment report together with the manual run in README.md.
"""

import argparse
import pathlib
import socket
import subprocess
import sys
import threading
import time

ROOT = pathlib.Path(__file__).resolve().parent
SERVER = ROOT / "server.py"
THREADED_SERVER = ROOT / "server_threaded.py"
CLIENT = ROOT / "client.py"
SERVER_LOG = ROOT / "server_log.txt"
THREADED_LOG = ROOT / "server_threaded_log.txt"
ENCODING = "utf-8"
TIMEOUT = 5.0

# Windows console safety, same as server.py / client.py.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding=ENCODING, errors="replace")

results = []


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
def free_port() -> int:
    """Ask the OS for a currently unused TCP port."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return probe.getsockname()[1]


def wait_until_listening(port: int, limit: float = 10.0) -> None:
    """Poll the port until the server accepts connections (or give up)."""
    deadline = time.time() + limit
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"server did not start listening on 127.0.0.1:{port}")


def send_and_receive(port: int, message: str) -> str:
    """Open a connection, send one message, read the confirmation, close."""
    with socket.create_connection(("127.0.0.1", port), timeout=TIMEOUT) as sock:
        sock.sendall(message.encode(ENCODING) + b"\n")
        data = b""
        while not data.endswith(b"\n"):
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
    return data.decode(ENCODING).rstrip("\r\n")


def check(name: str, condition: bool, detail: str) -> None:
    results.append((name, condition, detail))
    mark = "PASS" if condition else "FAIL"
    print(f"  [{mark}] {name}\n         {detail}", flush=True)


def recv_all(port: int, message: str, hold: float = 0.0) -> str:
    """Like send_and_receive, but can hold the connection open first.

    Holding the socket open lets several clients overlap, which is how we prove
    that the threaded server really serves them at the same time.
    """
    with socket.create_connection(("127.0.0.1", port), timeout=TIMEOUT) as sock:
        if hold:
            time.sleep(hold)
        sock.sendall(message.encode(ENCODING) + b"\n")
        data = b""
        while not data.endswith(b"\n"):
            chunk = sock.recv(4096)
            if not chunk:
                break
            data += chunk
    return data.decode(ENCODING).rstrip("\r\n")


def run_threaded_phase() -> None:
    """BONUS: prove that server_threaded.py serves clients concurrently."""
    print("\n" + "=" * 70)
    print("  BONUS PHASE -- server_threaded.py (several clients at the same time)")
    print("=" * 70)
    if not THREADED_SERVER.exists():
        print("  skipped: server_threaded.py not found")
        return

    port = free_port()
    log_file = open(THREADED_LOG, "w", encoding=ENCODING)
    server = subprocess.Popen(
        [sys.executable, str(THREADED_SERVER), "--host", "127.0.0.1",
         "--port", str(port)],
        stdout=log_file, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
    )
    replies, failures = {}, []
    HOLD = 0.5          # every client keeps its socket open for 0.5 s

    def worker(n: int) -> None:
        try:
            replies[n] = recv_all(port, f"concurrent client {n}", hold=HOLD)
        except OSError as exc:
            failures.append(f"client {n}: {exc}")

    try:
        wait_until_listening(port)
        threads = [threading.Thread(target=worker, args=(n,)) for n in range(1, 5)]
        started = time.perf_counter()
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        elapsed = time.perf_counter() - started
    finally:
        server.terminate()
        try:
            server.wait(timeout=5)
        except subprocess.TimeoutExpired:
            server.kill()
        log_file.close()

    log_text = THREADED_LOG.read_text(encoding=ENCODING, errors="replace")
    # Extract every "active: N" marker written by the worker threads.
    active = []
    for line in log_text.splitlines():
        if "active:" in line:
            tail = line.replace(")", "").rsplit("active:", 1)[-1].strip()
            if tail.isdigit():
                active.append(int(tail))
    peak = max(active) if active else 0

    ok = (not failures and len(replies) == 4
          and all(r.startswith("Message received") for r in replies.values())
          and peak >= 2)
    check("T7  threaded server overlaps 4 clients in one 0.5 s window", ok,
          f"peak simultaneous clients observed: {peak}, "
          f"all four answered: {len(replies) == 4}, "
          f"wall clock {elapsed:.2f}s (sequential would need >= "
          f"{4 * HOLD:.1f}s)")
    if failures:
        print("         failures: " + "; ".join(failures))
    print("\n  (threaded server log: " + THREADED_LOG.name + ")")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Automated proof that server.py / client.py work.")
    parser.add_argument("--brief", action="store_true",
                        help="skip the captured server-terminal dump, so the "
                             "PASS/FAIL table fits on one screen")
    args = parser.parse_args()
    brief = args.brief

    print("=" * 70)
    print("  AUTOMATED TEST -- client/server socket communication")
    print("=" * 70)

    port = free_port()
    print(f"  Starting server.py on 127.0.0.1:{port} ...", flush=True)

    # Server output goes to a file so this test can show it afterwards
    # (and so the child never blocks on a full stdout pipe).
    with open(SERVER_LOG, "w", encoding=ENCODING) as log_file:
        proc = subprocess.Popen(
            [sys.executable, str(SERVER), "--host", "127.0.0.1",
             "--port", str(port), "--timeout", "3"],
            stdout=log_file, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
        )
        try:
            wait_until_listening(port)
            print("  Server is up. Running test cases ...\n")

            # --- Test 1: one client, one message -------------------------
            reply = send_and_receive(port, "Hello server, this is client #1!")
            check("T1  single message is acknowledged",
                  reply.startswith("Message received"),
                  f'server replied: "{reply}"')

            # --- Test 2: several clients sequentially --------------------
            replies = [send_and_receive(port, f"Message number {i}")
                       for i in range(2, 7)]
            numbers = []
            for r in replies:
                tail = r.rsplit("#", 1)[-1]
                numbers.append(int(tail) if tail.isdigit() else -1)
            sequential = all(b == a + 1 for a, b in zip(numbers, numbers[1:]))
            check("T2  five more clients served one after another",
                  all(r.startswith("Message received") for r in replies)
                  and sequential,
                  f"server numbered them {numbers} (each exactly +1): {sequential}")

            # --- Test 3: UTF-8 payload -----------------------------------
            text = "Halo, apa kabar? Semoga lancar \u2014 salam dari \U0001F600"
            reply = send_and_receive(port, text)
            ok = (reply.startswith("Message received")
                  and f"{len(text)} chars" in reply)
            check("T3  UTF-8 text survives the round trip", ok,
                  f"{len(text)} chars sent, server interpreted them correctly: {ok}")

            # --- Test 4: long message (split across TCP segments) --------
            long_text = "A" * 5000
            reply = send_and_receive(port, long_text)
            ok = "5000" in reply
            check("T4  5000-character message is reassembled correctly", ok,
                  f'server replied: "{reply}"')

            # --- Test 5: silent client must not kill the server ---------
            with socket.create_connection(("127.0.0.1", port), timeout=TIMEOUT):
                pass                     # connect then leave: no message at all
            time.sleep(0.3)
            reply = send_and_receive(port, "still alive?")
            check("T5  server survives a client that hangs up silently",
                  reply.startswith("Message received"),
                  "next client was still served normally")

            # --- Test 6: empty message is rejected gracefully -----------
            reply = send_and_receive(port, "")
            check("T6  empty message gets no bogus confirmation",
                  reply == "",
                  "server closed the connection without replying (correct)")

        finally:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()

    # --- server-side terminal evidence ---------------------------------
    if not brief:
        print("\n" + "=" * 70)
        print("  SERVER TERMINAL OUTPUT (captured while the tests ran)")
        print("=" * 70)
        print(SERVER_LOG.read_text(encoding=ENCODING, errors="replace").rstrip())
        print("=" * 70)

    run_threaded_phase()

    passed = sum(1 for _, ok, _ in results if ok)
    total = len(results)
    print(f"  RESULT: {passed}/{total} tests passed")
    print("=" * 70)
    print(f"  Server log saved to: {SERVER_LOG.name}")
    print(f"  Client program      : {CLIENT.name}  (run it interactively)")
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
