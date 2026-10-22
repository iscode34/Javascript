"""three clients that stay connected at the same time, for the threaded figure."""
import socket
import sys
import threading
import time

port = int(sys.argv[1])
barrier = threading.Barrier(3)


def client(n):
    with socket.create_connection(("127.0.0.1", port), timeout=10) as s:
        barrier.wait(timeout=5)          # all three connected at once
        for msg in (f"client {n}: halo", f"client {n}: pesan kedua"):
            s.sendall(msg.encode() + b"\n")
            data = b""
            while not data.endswith(b"\n"):
                chunk = s.recv(4096)
                if not chunk:
                    break
                data += chunk
            print(f"  client {n} <- {data.decode().strip()}", flush=True)
            time.sleep(0.25)


threads = [threading.Thread(target=client, args=(n,)) for n in (1, 2, 3)]
for t in threads:
    t.start()
for t in threads:
    t.join()
print("all three clients done")
