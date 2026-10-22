# Inter-Process Communication with Sockets — Client / Server Project

| | |
|---|---|
| **Course** | Parallel and Distributed Systems |
| **Session** | 3 (third) — Inter-Process Communication |
| **Lecturer** | Muchtar Ali Setyo Yudono, S.T., M.T. |
| **Task type** | Case Based / Project Based |
| **Language** | Python 3 (standard library only — `socket`, `time`) |
| **Name / NIM** | Mohammad Istahad Alam Chowdhury / 20250040225 (TI25I) |

Two programs — a **server** that acts as the central hub and a **client** that sends
text messages to it — plus a bonus concurrent server and automated proof that
everything works. Every transcript in this README was produced by actually
running the programs on Windows (Python 3.13.5), not written by hand.

---

## 0. How to use it (the short version)

**The easy way — one double-click:** open the folder and double-click
**`start_demo.bat`**. Two windows open by themselves: the server (leave it
alone) and the client (type there). That is the whole demo.

**The manual way — two windows:**

1. Open a terminal in this folder and start the server:
   ```
   python server.py
   ```
   It prints `Waiting for a client to connect ...` and keeps running.
2. Open a **second** terminal in the same folder and start the client:
   ```
   python client.py
   ```
3. In the client window type a message and press **Enter**. The server window
   shows what you sent plus your IP address and the time, and the client shows
   `Server > Message received (...)`. Type as many messages as you like.
4. Type `/quit` in the client to close the connection, and press `Ctrl+C` in the
   server window to stop it.

> **Why does `localhost:5000` in a browser show nothing?**
> Because this is not a web server. A browser sends an HTTP request and expects
> an HTML page back; our server only speaks the little newline-based text
> protocol described in §5 below. The only program that can talk to it is
> `client.py`. (A browser showing nothing is, in fact, the correct behaviour.)

To let a **second device** connect, start the server normally and give the client
the server machine's IP:

```
python client.py --host 192.168.1.10
```

---

## 1. What is in this folder

| File | Purpose |
|---|---|
| `start_demo.bat` | **One double-click** opens the server and the client in two windows (optional port as first argument: `start_demo.bat 5000`). |
| `Report_InterProcessCommunication.docx` | **Submission report (Word, 6 pages)** — English, written in first person: introduction, how the two programs talk, both programs, how to run them, tests, problems, conclusion. |
| `Report_InterProcessCommunication.pdf` | The same report as PDF, ready to upload. |
| `server.py` | **Task 1.** Sequential TCP server: accepts a client, prints its message, replies "Message received", closes the connection, then waits for the next client. |
| `client.py` | **Task 2.** Interactive client: connects, lets the user type messages in a loop, prints each confirmation from the server, closes cleanly. |
| `server_threaded.py` | **Bonus.** Same protocol, but one thread per client — several clients are served *simultaneously* instead of one after another. |
| `demo_test.py` | Automated test suite (7 cases). Starts the real server, drives real sockets, prints PASS/FAIL and the server's own terminal output. Use `--brief` to see just the PASS/FAIL table. |
| `demo_interactive.py` | Reproduces a full "two terminals side by side" session and prints both terminals' output. |
| `server_log.txt`, `server_log_keepalive.txt`, `server_threaded_log.txt` | Server-side terminal output captured by the demo scripts. |
| `demo_test_output.txt`, `demo_interactive_output.txt` | Captured output of the two scripts (evidence for the report). |
| `shots/` | The figures used in the report: `fig_arch.png`, `fig_sequence.png` (drawn diagrams) and `fig1_client.png` … `fig4_threaded.png` — **real screenshots** of the running programs, captured by `shots/capture_session.ps1`. |
| `build_report.py` | Regenerates the DOCX from the sources and the screenshots (`python build_report.py`). |

---

## 2. Options and non-interactive runs

You need Python 3.7+. Both programs run from this folder; the server must be
started before the client (the basic steps are in §0).

Ports and behaviour are configurable:

```bash
python server.py --port 8080                  # listen on another port
python server.py --messages 0                 # keep one connection open
python server.py --timeout 10                 # drop a silent client sooner
python client.py --port 8080                  # client must use the same port
python client.py --host 192.168.1.10          # server on another device
```

Automated proof (no typing needed):

```bash
python demo_test.py            # 7 tests, exit code 0 = all passed
python demo_test.py --brief    # only the PASS/FAIL table, no server dump
python demo_interactive.py     # full conversation, both terminals
```

---

## 3. Task 1 — `server.py`

The program follows the suggested steps one to one:

| Task step | Where in the code |
|---|---|
| Import `socket` and `time` | top of the file (plus `argparse`, `sys`) |
| Create socket, bind to IP + port | `create_server()` — `socket.socket(AF_INET, SOCK_STREAM)`, `bind()`, `listen()` |
| Listen for and accept connections | `server.accept()` inside the `while True` loop of `main()` |
| Receive the message, print it | `recv_message()` + the `print` block in `handle_client()` |
| Send the confirmation back | `send_message(conn, reply)` — `"Message received (...)"` |
| Close the connection properly | `with conn:` in `main()` + `server.close()` in `finally` |
| Handle multiple clients **sequentially** | one `accept()` → serve → close → `accept()` again |

Terminal output of the server while clients talk to it:

```text
==============================================================
  SOCKET SERVER -- Inter-Process Communication (Session 3)
==============================================================
  Listening on  : 0.0.0.0:5000
  Local IP hint : 192.168.101.3
  Clients       : sequential (one at a time)
  Per connection: 1 message per connection, then close (task spec)
  Client timeout: 30 s
  Press Ctrl+C to shut the server down.
==============================================================
[13:24:04] Waiting for a client to connect ...
==============================================================
[13:24:04] Client #2 connected from 127.0.0.1:2419
    accepted at 2026-10-22 13:24:04
[13:24:04] Message from client #2 (127.0.0.1:2419):
    "Halo server, ini pesan pertama dari client."
    length : 43 characters (43 bytes on the wire)
    arrived: 2026-10-22 13:24:04 (read in 0.4 ms)
[13:24:04] Confirmation sent to client #2: "Message received (43 chars / 43 bytes) - thank you, client #2"
[13:24:04] Connection with client #2 closed (1 message(s) served)
```

The server prints, for every message: **who** sent it (IP:port), **what** it said,
**how long** it was, and **when** it arrived — the "central hub that displays the
received messages in the terminal" the scenario asks for.

Every option:

| Flag | Default | Meaning |
|---|---|---|
| `--host` | `0.0.0.0` | Address to bind. `0.0.0.0` = all interfaces (reachable from the LAN); `127.0.0.1` = localhost only. |
| `--port` | `5000` | TCP port. Use > 1023 so no administrator rights are needed. |
| `--timeout` | `30` | Seconds to wait for one client. Prevents a silent client from blocking the server forever. |
| `--messages` | `1` | Messages per connection before closing. `1` is the behaviour the task asks for; `0` keeps the connection open until the client hangs up. |

---

## 4. Task 2 — `client.py`

| Task step | Where in the code |
|---|---|
| Import `socket` | top of the file |
| Create socket and connect to IP + port | `connect()` — `socket.socket(...)`, `connect((host, port))` |
| Send a user-provided text message | `send_message()` inside the input loop |
| Receive and display the server's response | `recv_message()` → `print(f"Server > {reply}")` |
| Allow repeated input in a loop | `while True:` around `input("\nYou > ")` |
| Handle proper closure | `finally: close_quietly(sock)` — `shutdown()` then `close()` |

What the user sees:

```text
==============================================================
  SOCKET CLIENT -- Inter-Process Communication (Session 3)
==============================================================
  Connecting to : 127.0.0.1:2415
  Connected!     : local endpoint 127.0.0.1:2419
  Type a message and press Enter.  /quit to exit.
==============================================================

You > Halo server, ini pesan pertama dari client.
Server > Message received (43 chars / 43 bytes) - thank you, client #2
         (round-trip time: 0.70 ms)

You > Pesan kedua: uji komunikasi dua arah.
  (server closed the previous connection -- reconnecting ...)
Server > Message received (37 chars / 37 bytes) - thank you, client #3
         (round-trip time: 1.42 ms, after one reconnect)
```

In-chat commands: `/quit`, `/exit`, `:q` — close and leave. An empty line is
ignored (nothing is sent). The round-trip time is measured with
`time.perf_counter()` and shows how fast the acknowledgement comes back.

---

## 5. How the communication actually works

```text
            client.py                                  server.py
   ┌───────────────────────────┐            ┌───────────────────────────────┐
   │ socket()                  │            │ socket()                      │
   │ connect(host, 5000)  ─────┼── SYN ────▶│ bind(0.0.0.0, 5000)           │
   │                           │◀─ SYN/ACK ─│ listen(5)                     │
   │   (TCP connection ready)  │─── ACK ───▶│ accept() ──▶ conn, addr       │
   │                           │            │                               │
   │ sendall("Halo" + "\n") ───┼───────────▶│ recv() → "Halo"               │
   │                           │            │ print(...)  ← terminal output │
   │                           │            │ sendall("Message received\n") │
   │ recv() → reply            │◀───────────┼───────────────                │
   │ print("Server > ...")     │            │ close(conn)  (1 msg per conn) │
   │                           │            │ accept() again ...            │
   │ shutdown() + close()      │            │                               │
   └───────────────────────────┘            └───────────────────────────────┘
```

Key ideas demonstrated:

* **Socket = endpoint of a connection.** `AF_INET` + `SOCK_STREAM` means TCP/IPv4:
  ordered, reliable, connection-oriented bytes.
* **The server side** must `bind()` a known address/port, `listen()` to declare
  it passive, and `accept()` to obtain a *new* socket dedicated to one client.
  The listening socket stays open the whole time, which is why the server can
  keep serving clients forever.
* **TCP is a byte stream, not a message stream.** One `send()` may be delivered
  as several `recv()` fragments, so both programs use a **newline delimiter**
  and loop until the `\n` arrives. This is the single most common bug in socket
  assignments — the test case T4 (a 5000-character message) proves the framing
  works.
* **`sendall()` instead of `send()`**, because `send()` may transmit only part of
  the buffer.
* **`SO_REUSEADDR`** so the port can be reused immediately after a restart
  (otherwise Windows reports *WinError 10048, address already in use*).
* **`with conn:` / `finally:`** guarantee that sockets are closed even when
  something fails — leaked descriptors eventually make `accept()` fail.

---

## 6. Test results — `python demo_test.py`

All seven cases pass against the real programs (`exit code 0`):

| # | Test case | What it proves | Result |
|---|---|---|---|
| T1 | One client sends one message | Basic request → acknowledgement works | **PASS** |
| T2 | Five clients, one after another | Sequential handling; server numbers them 3, 4, 5, 6, 7 (+1 each) | **PASS** |
| T3 | UTF-8 text (`é`, emoji) | Encoding is correct end to end | **PASS** |
| T4 | 5000-character message | Chunked reads are reassembled correctly | **PASS** |
| T5 | Client that connects and hangs up | Server survives and keeps serving | **PASS** |
| T6 | Empty message | No bogus acknowledgement; connection closed gracefully | **PASS** |
| T7 | Bonus: 4 clients inside one 0.5 s window | Threaded server overlaps them (peak 4 active, 0.52 s instead of ≥ 2.0 s) | **PASS** |

```text
  [PASS] T1  single message is acknowledged
         server replied: "Message received (32 chars / 32 bytes) - thank you, client #2"
  [PASS] T2  five more clients served one after another
         server numbered them [3, 4, 5, 6, 7] (each exactly +1): True
  [PASS] T3  UTF-8 text survives the round trip
         45 chars sent, server interpreted them correctly: True
  [PASS] T4  5000-character message is reassembled correctly
         server replied: "Message received (5000 chars / 5000 bytes) - thank you, client #9"
  [PASS] T5  server survives a client that hangs up silently
         next client was still served normally
  [PASS] T6  empty message gets no bogus confirmation
         server closed the connection without replying (correct)
  [PASS] T7  threaded server overlaps 4 clients in one 0.5 s window
         peak simultaneous clients observed: 4, all four answered: True, wall clock 0.52s

  RESULT: 7/7 tests passed
```

---

## 7. Two requirements that pull in opposite directions (and the fix)

The task says two things that are easy to write and hard to combine:

* **Task 1** — the server answers, then **closes** the connection and moves on.
* **Task 2** — the client must send messages **in a loop**, repeatedly.

If you implement both literally, the second message hits a socket the server has
already closed. On Windows that is exactly
`[WinError 10053] An established connection was aborted by the software in your
host machine` — and the naive client dies after one message. Three honest ways
to solve it, and this project supports the two most useful ones:

1. **The client reconnects (default in `client.py`).** When it detects the dead
   connection (error 10053/10054, or an empty read), it opens a fresh socket and
   re-sends the message once. The user keeps typing and never notices. Cost: one
   extra TCP handshake per message (visible as "after one reconnect").
2. **The server keeps the connection open ( `--messages 0` ).** Now all messages
   travel over one connection — fewer handshakes, and this is what real chat
   servers do. `demo_interactive.py` phase B shows this mode.
3. *(Out of scope here)* multiplexing many clients at once — that is the bonus
   `server_threaded.py`, which combines concurrency with a persistent connection.

```text
PHASE A -- default server (1 message per connection, client reconnects)
  You > Server > Message received (43 chars / 43 bytes) - thank you, client #2
  You >   (server closed the previous connection -- reconnecting ...)
  Server > Message received (37 chars / 37 bytes) - thank you, client #3
  You >   (server closed the previous connection -- reconnecting ...)
  Server > Message received (44 chars / 50 bytes) - thank you, client #4

PHASE B -- server.py --messages 0 (one connection for all three messages)
  You > Server > Message received (43 chars / 43 bytes) - thank you, client #2
  You > Server > Message received (37 chars / 37 bytes) - thank you, client #2
  You > Server > Message received (44 chars / 50 bytes) - thank you, client #2
```

---

## 8. Limitation of a sequential server, and the bonus fix

A sequential server (`server.py`) is correct but slow by construction:

* while client #1 is connected, clients #2…N sit in the OS accept queue;
* a client that connects and never sends anything blocks everyone — that is why
  `--timeout` exists (the test T5/T6 exercise this path);
* one crashed handler would take the whole server down.

`server_threaded.py` fixes the first point with `threading.Thread` per accepted
connection, a `threading.Lock` around the shared client counter, and
`daemon=True` so threads never keep the process alive. Each worker also keeps
its connection **open**, so a client gets many messages answered over one
session (concurrent *and* persistent). Same wire protocol, so `client.py` works
with either server unchanged:

```bash
python server_threaded.py            # listens on :5001 by default
python client.py --port 5001
```

Measured in test T7: four clients that each hold their socket open for 0.5 s are
all served in **0.52 s**; the sequential server would need **≥ 2.0 s**.

---

## 9. Running across two devices (the real "distributed" case)

1. Find the server machine's IP: `ipconfig` (Windows) / `ip addr` (Linux).
   Example: `192.168.1.10`.
2. Start the server there: `python server.py` (it binds `0.0.0.0`, so it already
   accepts connections from the LAN).
3. Allow Python through the firewall (Windows, admin terminal):
   `netsh advfirewall firewall add rule name="PySocket 5000" dir=in action=allow protocol=TCP localport=5000`
4. On the second device: `python client.py --host 192.168.1.10`
5. Both devices must be on the same network, and the router must not isolate
   wireless clients (guest networks often do).

If the connection is refused, check in this order: server running? → port equal
on both sides? → firewall rule? → correct IP (not `127.0.0.1` on the wrong
machine)?

---

## 10. Problems found while testing this project

These were not hypothetical; each one was observed, then fixed, then re-tested:

| Symptom | Cause | Fix |
|---|---|---|
| `UnicodeEncodeError: 'charmap' codec can't encode character '\U0001f600'` — the server crashed on an emoji, which looked like a network failure | Windows console defaults to the legacy cp1252 code page | `sys.stdout.reconfigure(encoding="utf-8", errors="replace")` in all three programs |
| Client crashed with `WinError 10053` on its second message | The server closes after each acknowledgement (by design) | Client detects the dead socket, reconnects and re-sends once (§7) |
| Accented letters/emoji arrived mangled when input was piped | `sys.stdin` on Windows decodes piped input as cp1252 | `sys.stdin.reconfigure(encoding="utf-8")` in `client.py` |
| Message truncated for long input | One `recv()` does not have to return a whole message | Newline delimiter + read loop in `recv_message()` |
| `OSError: [WinError 10048] address already in use` after restarting the server | OS holds the port briefly | `setsockopt(SO_REUSEADDR, 1)` |

---

## 11. Checklist against the assignment

**Task 1 — server**

- [x] Uses Python's `socket` library (and `time` for timestamps)
- [x] Creates a socket, binds it to an IP address and a port, listens
- [x] Accepts incoming client connections
- [x] Receives the client's message and displays it in the server terminal
- [x] Sends a confirmation back (`"Message received (...)"`)
- [x] Closes the connection properly after responding
- [x] Handles multiple clients **sequentially** (one at a time, then the next)

**Task 2 — client**

- [x] Uses Python's `socket` library
- [x] Connects to the server's IP address and port
- [x] Sends a user-provided text message
- [x] Waits for and displays the server's response
- [x] Lets the user send messages repeatedly in a loop
- [x] Closes the connection properly on `/quit`, Ctrl+C and on errors

**Extra (not required, kept for marks/understanding):** bonus multithreaded
server with measured concurrency, 7-case automated test suite, reproducible
two-terminal transcript generator, LAN/firewall instructions, and documented
bug fixes for the platform-specific traps above.
