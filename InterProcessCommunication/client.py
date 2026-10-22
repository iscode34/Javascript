#!/usr/bin/env python3
"""
client.py -- Task 2: Socket client for the Inter-Process Communication assignment.

Course      : Parallel and Distributed Systems
Session     : 3 -- Inter-Process Communication
Lecturer    : Muchtar Ali Setyo Yudono, S.T., M.T.
Type        : Case Based / Project Based

What this program does
----------------------
1. Creates a TCP socket and connects it to the server's IP address + port.
2. Asks the user for a text message, in a loop, until the user types /quit.
3. Sends each message to the server.
4. Waits for the server's confirmation and prints it on the terminal.
5. Closes the connection properly on exit (including Ctrl+C).

One important detail about "repeated communication"
---------------------------------------------------
Task 1 says the server must answer one client and then close the connection.
Task 2 says the client must be able to keep sending messages in a loop.
Those two rules only work together if the client reconnects when it notices
that the server closed the socket. As soon as this client detects a dead
connection (Windows error 10053/10054, or an empty read), it opens a fresh
connection and re-sends the message -- so the user can keep typing without
ever restarting the program.

Run it
------
    python client.py                              # 127.0.0.1:5000
    python client.py --host 192.168.1.10          # server on the LAN
    python client.py --host 192.168.1.10 --port 8080

In-chat commands
----------------
    /quit   or  /exit   -> close the connection and leave
    (empty line)        -> ignored, nothing is sent
"""

import argparse
import socket
import sys
import time

# ---------------------------------------------------------------------------
# Configuration (defaults). Point --host at the server machine's IP address
# when the two programs run on different devices.
# ---------------------------------------------------------------------------
HOST = "127.0.0.1"      # localhost; use the server's LAN IP for a second device
PORT = 5000             # must match the port used by server.py
BUFFER_SIZE = 4096      # bytes read per recv() call
ENCODING = "utf-8"      # text encoding used by both sides
QUIT_COMMANDS = {"/quit", "/exit", ":q"}

# Windows terminals still default to a legacy code page that cannot encode all
# characters; force UTF-8 so printing any server reply never raises.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding=ENCODING, errors="replace")
# Same for stdin: when input is piped or redirected it must be decoded as
# UTF-8, otherwise accented letters and emoji arrive mangled on the server.
if hasattr(sys.stdin, "reconfigure"):
    try:
        sys.stdin.reconfigure(encoding=ENCODING, errors="replace")
    except (AttributeError, ValueError):    # e.g. some IDEs / frozen stdio
        pass


def recv_message(sock: socket.socket) -> str:
    """
    Receive exactly one newline-terminated message from the server.

    Same delimiter logic as the server side: accumulate bytes until the "\\n"
    terminator arrives, because one message may be split across several TCP
    segments. Returns "" if the server closed the connection.
    """
    data = b""
    while not data.endswith(b"\n"):
        chunk = sock.recv(BUFFER_SIZE)
        if not chunk:            # server closed the connection
            break
        data += chunk
    return data.decode(ENCODING, errors="replace").rstrip("\r\n")


def send_message(sock: socket.socket, text: str) -> None:
    """Send one newline-terminated UTF-8 message (sendall = never truncates)."""
    sock.sendall(text.encode(ENCODING) + b"\n")


def connect(host: str, port: int) -> socket.socket:
    """Create the client socket and connect it to the server (connect(host,port))."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))   # blocks until the TCP handshake succeeds
    return sock


def close_quietly(sock: "socket.socket | None") -> None:
    """Close a socket without ever raising (used on exit and on reconnects)."""
    if sock is None:
        return
    try:
        sock.shutdown(socket.SHUT_RDWR)   # tell the peer "no more data"
    except OSError:
        pass                              # already closed by the server
    try:
        sock.close()
    except OSError:
        pass


def exchange(host: str, port: int, sock: socket.socket, message: str):
    """
    Send one message and read the server's confirmation.

    Returns (socket, reply, reconnected). If the server has closed the previous
    connection (normal for this sequential server), the message is re-sent once
    over a brand-new connection, so the user never has to restart the client.
    """
    reconnected = False
    for attempt in (1, 2):
        try:
            send_message(sock, message)
            reply = recv_message(sock)
            if reply:
                return sock, reply, reconnected
            # Empty read -> the server closed the socket without answering.
            raise ConnectionError("server closed the connection without replying")
        except OSError:
            if attempt == 2:          # reconnect did not help either -> give up
                raise
            print("  (server closed the previous connection -- reconnecting ...)",
                  flush=True)
            close_quietly(sock)
            sock = connect(host, port)
            reconnected = True
    raise RuntimeError("unreachable")      # pragma: no cover


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Interactive TCP client (Inter-Process Communication demo).")
    parser.add_argument("--host", default=HOST,
                        help=f"server IP address (default: {HOST})")
    parser.add_argument("--port", type=int, default=PORT,
                        help=f"server port (default: {PORT})")
    args = parser.parse_args()

    print("=" * 62)
    print("  SOCKET CLIENT -- Inter-Process Communication (Session 3)")
    print("=" * 62)
    print(f"  Connecting to : {args.host}:{args.port}")

    sock = None
    try:
        sock = connect(args.host, args.port)
    except ConnectionRefusedError:
        print(f"[ERROR] Connection refused by {args.host}:{args.port}.")
        print("        The server is not running or the port does not match.")
        print("        Start it first:  python server.py")
        return 1
    except socket.timeout:
        print(f"[ERROR] Timed out while connecting to {args.host}:{args.port}.")
        print("        Check the IP address and the firewall.")
        return 1
    except OSError as exc:
        print(f"[ERROR] Cannot reach {args.host}:{args.port} -> {exc}")
        return 1

    local_ip, local_port = sock.getsockname()
    print(f"  Connected!     : local endpoint {local_ip}:{local_port}")
    print("  Type a message and press Enter.  /quit to exit.")
    print("=" * 62, flush=True)

    sent = 0
    try:
        while True:                                   # loop: repeated communication
            try:
                message = input("\nYou > ").strip()
            except EOFError:                          # Ctrl+Z / piped input ended
                break

            if not message:
                continue                              # ignore empty lines
            if message.lower() in QUIT_COMMANDS:
                break

            started = time.perf_counter()
            try:
                sock, reply, reconnected = exchange(
                    args.host, args.port, sock, message)   # 1) send 2) receive
            except ConnectionRefusedError:
                print(f"[ERROR] Server at {args.host}:{args.port} is no longer "
                      f"running -- message not delivered.")
                break
            except OSError as exc:
                print(f"[ERROR] Communication error -> {exc}")
                break
            rtt_ms = (time.perf_counter() - started) * 1000
            sent += 1

            print(f"Server > {reply}")
            print(f"         (round-trip time: {rtt_ms:.2f} ms"
                  f"{', after one reconnect' if reconnected else ''})")
    except KeyboardInterrupt:
        print("\n[INFO] Ctrl+C received -- closing the connection.")
    finally:
        close_quietly(sock)                           # step 5: proper closure
        print(f"[INFO] Connection closed. Messages sent this session: {sent}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
