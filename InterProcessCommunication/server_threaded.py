#!/usr/bin/env python3
"""
server_threaded.py -- BONUS: concurrent version of the server (multi-client).

The assignment asks for a SEQUENTIAL server (see server.py): it serves one
client, then moves on to the next. That is perfect for learning the socket
API, but it has one well-known weakness:

    while client #1 is connected, clients #2..#N are kept waiting; and if
    client #1 never sends anything, it blocks everyone (until our timeout).

This file shows how far a small change gets you: one thread per connection.
Now N clients are served truly at the same time, and a slow client cannot
block the others. The wire protocol is identical, so client.py works with
BOTH servers without any change.

Run it
------
    python server_threaded.py            # 0.0.0.0:5001 (different port by default)
    python client.py --port 5001
"""

import argparse
import socket
import sys
import threading
import time

HOST = "0.0.0.0"
PORT = 5001            # 5001 so it can run side by side with server.py
BACKLOG = 50
BUFFER_SIZE = 4096
ENCODING = "utf-8"

# Same Windows console fix as server.py: never let a print() kill a thread.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding=ENCODING, errors="replace")

_lock = threading.Lock()      # guards _client_no (shared mutable state)
_client_no = 0
_active = 0


def log(message: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def recv_message(conn: socket.socket) -> str:
    """Read one newline-terminated message (TCP is a byte stream, so loop)."""
    data = b""
    while not data.endswith(b"\n"):
        chunk = conn.recv(BUFFER_SIZE)
        if not chunk:
            break
        data += chunk
    return data.decode(ENCODING, errors="replace").rstrip("\r\n")


def handle_client(conn: socket.socket, addr: tuple, client_no: int) -> None:
    """Body of one worker thread: serve one client, then the thread ends."""
    global _active
    peer = f"{addr[0]}:{addr[1]}"
    with _lock:
        _active += 1
        active_now = _active
    log(f"[thread {threading.current_thread().name}] client #{client_no} "
        f"connected from {peer} (active: {active_now})")
    try:
        with conn:
            served = 0
            # Persistent connection: keep answering this client until it hangs
            # up. That is what a real chat hub does, and it is the point of the
            # threaded design -- many clients, each with an open session.
            while True:
                message = recv_message(conn)
                if not message:
                    if served == 0:
                        log(f"client #{client_no} ({peer}) left without "
                            f"sending data")
                    else:
                        log(f"client #{client_no} ({peer}) hung up after "
                            f"{served} message(s)")
                    return
                served += 1
                log(f"client #{client_no} ({peer}) sent: \"{message}\"")
                reply = (f"Message received ({len(message)} chars / "
                         f"{len(message.encode(ENCODING))} bytes) - "
                         f"thank you, client #{client_no}")
                conn.sendall(reply.encode(ENCODING) + b"\n")
                log(f"confirmation sent to client #{client_no} "
                    f"(message {served})")
    except (ConnectionResetError, BrokenPipeError):
        log(f"client #{client_no} ({peer}) reset the connection")
    except OSError as exc:
        log(f"socket error on client #{client_no}: {exc}")
    finally:
        with _lock:
            _active -= 1
            active_now = _active
        log(f"client #{client_no} ({peer}) done (active: {active_now})")


def main() -> int:
    global _client_no
    parser = argparse.ArgumentParser(description="Concurrent (threaded) TCP server.")
    parser.add_argument("--host", default=HOST)
    parser.add_argument("--port", type=int, default=PORT)
    args = parser.parse_args()

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server.bind((args.host, args.port))
    except OSError as exc:
        print(f"[ERROR] Cannot bind to {args.host}:{args.port} -> {exc}")
        return 1
    server.listen(BACKLOG)

    print("=" * 62)
    print("  THREADED SOCKET SERVER -- concurrent variant (bonus)")
    print("=" * 62)
    print(f"  Listening on : {args.host}:{args.port}")
    print("  Mode         : concurrent (one thread per client)")
    print("  Ctrl+C to stop.")
    print("=" * 62, flush=True)

    try:
        while True:
            conn, addr = server.accept()
            with _lock:
                _client_no += 1
                client_no = _client_no
            thread = threading.Thread(
                target=handle_client,
                args=(conn, addr, client_no),
                name=f"client-{client_no}",
                daemon=True,                 # never keeps the process alive
            )
            thread.start()
    except KeyboardInterrupt:
        print()
        log("Ctrl+C received -- shutting down.")
    finally:
        server.close()
        log(f"Server socket closed. Clients served: {_client_no}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
