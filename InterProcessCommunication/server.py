#!/usr/bin/env python3
"""
server.py -- Task 1: Socket server for the Inter-Process Communication assignment.

Course      : Parallel and Distributed Systems
Session     : 3 -- Inter-Process Communication
Lecturer    : Muchtar Ali Setyo Yudono, S.T., M.T.
Type        : Case Based / Project Based

What this program does
----------------------
1. Creates a TCP socket and binds it to an IP address + port.
2. Listens for incoming client connections.
3. Accepts ONE client at a time (sequential / iterative server), receives the
   text message, and prints it on the server terminal together with the
   client's address and the time it arrived.
4. Sends a confirmation back to the client, e.g. "Message received".
5. Closes that connection cleanly, then loops back to wait for the next client.

Protocol used
-------------
A tiny line-based protocol: every message is UTF-8 text terminated by "\\n".
This "newline as message boundary" rule is what allows one recv() call to be
split across several TCP segments without corrupting the message.

Run it
------
    python server.py                      # listens on 0.0.0.0:5000, one message
                                          #   per connection (as the task asks)
    python server.py --port 8080          # custom port
    python server.py --messages 0         # keep the connection open and keep
                                          #   answering the same client until it
                                          #   hangs up (alternative mode)
    python server.py --host 127.0.0.1 --port 5000 --timeout 15

Stop it with Ctrl+C.
"""

import argparse
import socket
import sys
import time

# ---------------------------------------------------------------------------
# Configuration (defaults). You can override host/port/timeout from the CLI.
# ---------------------------------------------------------------------------
HOST = "0.0.0.0"        # 0.0.0.0 = listen on every interface (LAN reachable)
PORT = 5000             # port the server listens on (use > 1023 without admin)
BACKLOG = 5             # how many pending connections the OS may queue
BUFFER_SIZE = 4096      # bytes read per recv() call
ENCODING = "utf-8"      # text encoding used by both sides
CLIENT_TIMEOUT = 30.0   # max seconds to wait for one client to say something
MAX_MESSAGES = 1        # 1 = answer, close, move on (task spec); 0 = unlimited

# Windows terminals still default to a legacy code page (e.g. cp1252) that
# cannot encode emoji or many non-Latin scripts. Printing such a message would
# crash the server with UnicodeEncodeError, which looks like a network bug but
# is only a console bug. Force UTF-8 output with a safe fallback character.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding=ENCODING, errors="replace")


def log(message: str) -> None:
    """Print a timestamped line on the server terminal (flushed immediately)."""
    print(f"[{time.strftime('%H:%M:%S')}] {message}", flush=True)


def rule(char: str = "-", width: int = 62) -> None:
    """Print a horizontal separator so the terminal output stays readable."""
    print(char * width, flush=True)


def recv_message(conn: socket.socket) -> str:
    """
    Receive exactly one newline-terminated message from the client.

    Returns the decoded text WITHOUT the trailing newline.
    Returns "" when the client closed the connection without sending anything.

    Why a loop? A single recv() is not guaranteed to return the whole message:
    TCP is a byte stream, so a short message may arrive in one piece while a
    long one may be split across several segments. We therefore accumulate
    bytes until we see the "\\n" delimiter (or the peer closes the socket).
    """
    data = b""
    while not data.endswith(b"\n"):
        chunk = conn.recv(BUFFER_SIZE)
        if not chunk:            # b"" means the peer closed its side (FIN)
            break
        data += chunk
    return data.decode(ENCODING, errors="replace").rstrip("\r\n")


def send_message(conn: socket.socket, text: str) -> None:
    """Send one newline-terminated UTF-8 message.

    sendall() is used instead of send() because send() may transmit only part
    of the buffer; sendall() keeps pushing until every byte is handed to the OS.
    """
    conn.sendall(text.encode(ENCODING) + b"\n")


def handle_client(conn: socket.socket, addr: tuple, client_no: int,
                  timeout: float, max_messages: int) -> None:
    """Serve one client: receive -> print -> acknowledge -> (close)."""
    peer = f"{addr[0]}:{addr[1]}"

    rule("=")
    log(f"Client #{client_no} connected from {peer}")
    print(f"    accepted at {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    # Timeout guard: this server is sequential, so a silent client would block
    # every other client forever. The timeout turns that into a clean skip.
    conn.settimeout(timeout)

    served = 0
    # max_messages == 1 -> the exact behaviour requested by Task 1:
    # answer once, close, then wait for the next client.
    # max_messages == 0 -> keep serving the same connection until it hangs up.
    while max_messages == 0 or served < max_messages:
        started = time.perf_counter()
        try:
            message = recv_message(conn)
        except socket.timeout:
            log(f"Client #{client_no} ({peer}) sent nothing within "
                f"{timeout:.0f}s -- dropping it")
            break

        if not message:
            # recv() returned b"" -> the client left without sending data.
            if served == 0:
                log(f"Client #{client_no} ({peer}) disconnected without "
                    f"sending data")
            else:
                log(f"Client #{client_no} ({peer}) closed the connection "
                    f"after {served} message(s)")
            break

        elapsed_ms = (time.perf_counter() - started) * 1000
        char_count = len(message)
        byte_count = len(message.encode(ENCODING))
        served += 1

        # --- Receive + display on the server terminal ----------------------
        log(f"Message from client #{client_no} ({peer}):")
        print(f'    "{message}"', flush=True)
        print(f"    length : {char_count} characters "
              f"({byte_count} bytes on the wire)", flush=True)
        print(f"    arrived: {time.strftime('%Y-%m-%d %H:%M:%S')} "
              f"(read in {elapsed_ms:.1f} ms)", flush=True)

        # --- Send the confirmation back to the client ----------------------
        reply = (f"Message received ({char_count} chars / {byte_count} bytes) "
                 f"- thank you, client #{client_no}")
        send_message(conn, reply)
        log(f"Confirmation sent to client #{client_no}: \"{reply}\"")

    log(f"Connection with client #{client_no} closed "
        f"({served} message(s) served)")


def create_server(host: str, port: int) -> socket.socket:
    """Create, configure and bind the listening socket (steps 1-2 of the task)."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # SO_REUSEADDR lets us restart the server immediately after a crash/restart
    # instead of hitting "OSError: [WinError 10048] address already in use".
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))     # reserve IP + port
    server.listen(BACKLOG)        # mark the socket as passive/listening
    return server


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Sequential TCP server (Inter-Process Communication demo).")
    parser.add_argument("--host", default=HOST,
                        help=f"IP address to bind (default: {HOST})")
    parser.add_argument("--port", type=int, default=PORT,
                        help=f"TCP port to listen on (default: {PORT})")
    parser.add_argument("--timeout", type=float, default=CLIENT_TIMEOUT,
                        help=f"seconds to wait for one client "
                             f"(default: {CLIENT_TIMEOUT})")
    parser.add_argument("--messages", type=int, default=MAX_MESSAGES,
                        help="messages to accept per connection before closing; "
                             "0 = keep the connection open until the client "
                             f"hangs up (default: {MAX_MESSAGES})")
    args = parser.parse_args()

    try:
        server = create_server(args.host, args.port)
    except OSError as exc:
        print(f"[ERROR] Cannot bind to {args.host}:{args.port} -> {exc}")
        print("        Is another program already using that port? "
              "Try --port 5001.")
        return 1

    mode = ("1 message per connection, then close (task spec)"
            if args.messages == 1 else
            f"{args.messages} messages per connection" if args.messages > 1
            else "keep the connection open until the client hangs up")

    print("=" * 62)
    print("  SOCKET SERVER -- Inter-Process Communication (Session 3)")
    print("=" * 62)
    print(f"  Listening on  : {args.host}:{args.port}")
    print(f"  Local IP hint : {socket.gethostbyname(socket.gethostname())}")
    print(f"  Clients       : sequential (one at a time)")
    print(f"  Per connection: {mode}")
    print(f"  Client timeout: {args.timeout:.0f} s")
    print("  Press Ctrl+C to shut the server down.")
    print("=" * 62, flush=True)

    client_no = 0
    try:
        while True:                       # step 3: accept clients one by one
            log("Waiting for a client to connect ...")
            conn, addr = server.accept()  # blocks until a client shows up
            client_no += 1
            with conn:                    # step 6: always closes the connection
                try:
                    handle_client(conn, addr, client_no, args.timeout,
                                  args.messages)
                except (ConnectionResetError, BrokenPipeError):
                    log(f"Client #{client_no} ({addr[0]}:{addr[1]}) "
                        f"reset the connection abruptly")
                except OSError as exc:
                    log(f"Socket error while serving client #{client_no}: {exc}")
            log(f"Clients served so far: {client_no}")
    except KeyboardInterrupt:
        print()
        log("Ctrl+C received -- shutting the server down.")
    finally:
        server.close()
        log(f"Server socket closed. Clients served this session: {client_no}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
