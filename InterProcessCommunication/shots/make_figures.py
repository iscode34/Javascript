"""make_figures.py -- draws the two diagrams used in the report (Pillow only)."""

import pathlib
from PIL import Image, ImageDraw, ImageFont

SHOTS = pathlib.Path(__file__).resolve().parent
FONTS = pathlib.Path(r"C:\Windows\Fonts")

INK = (31, 41, 55)
MUTED = (107, 114, 128)
ACCENT = (29, 78, 216)
ACCENT_SOFT = (239, 246, 255)
BOX_EDGE = (148, 163, 184)
GREEN = (21, 128, 61)
PANEL = (248, 250, 252)
LIFELINE = (203, 213, 225)


def font(name, size):
    for candidate in (name, "segoeui.ttf", "arial.ttf"):
        path = FONTS / candidate
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except OSError:
                continue
    return ImageFont.load_default()


def mono(size):
    return font("consola.ttf", size)


def bold(size):
    return font("segoeuib.ttf", size)


def regular(size):
    return font("segoeui.ttf", size)


def rounded(draw, box, radius=18, fill=None, outline=BOX_EDGE, width=2):
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=width)


def arrow(draw, start, end, color=ACCENT, width=3, head=15):
    x1, y1 = start
    x2, y2 = end
    draw.line((x1, y1, x2, y2), fill=color, width=width)
    sign = 1 if x2 > x1 else -1
    draw.polygon([(x2, y2), (x2 - sign * head, y2 - head // 2),
                  (x2 - sign * head, y2 + head // 2)], fill=color)


def dotted_vline(draw, x, y1, y2, color=LIFELINE):
    y = y1
    while y < y2:
        draw.line((x, y, x, min(y + 8, y2)), fill=color, width=2)
        y += 16


# ---------------------------------------------------------------------------
# Figure: architecture
# ---------------------------------------------------------------------------
def architecture():
    W, H = 1700, 820
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    d.text((60, 40), "Two processes, one TCP connection", font=bold(34), fill=INK)
    d.text((60, 88), "client.py and server.py are separate OS processes; the "
                     "socket is their shared endpoint.",
           font=regular(22), fill=MUTED)

    rounded(d, (60, 170, 620, 650), fill=ACCENT_SOFT)
    d.text((92, 196), "CLIENT PROCESS", font=bold(26), fill=ACCENT)
    d.text((92, 232), "client.py  (Python 3)", font=regular(20), fill=INK)
    for i, line in enumerate([
        "s = socket(AF_INET, SOCK_STREAM)",
        "s.connect(('127.0.0.1', 5000))",
        "",
        "s.sendall(msg + '\\n')",
        "reply = s.recv(4096)",
        "print('Server >', reply)",
        "",
        "s.shutdown(SHUT_RDWR)",
        "s.close()",
    ]):
        d.text((92, 282 + i * 33), line, font=mono(19), fill=INK)

    rounded(d, (1080, 170, 1640, 650), fill=ACCENT_SOFT)
    d.text((1112, 196), "SERVER PROCESS", font=bold(26), fill=ACCENT)
    d.text((1112, 232), "server.py  (Python 3)", font=regular(20), fill=INK)
    for i, line in enumerate([
        "s = socket(AF_INET, SOCK_STREAM)",
        "s.setsockopt(SO_REUSEADDR, 1)",
        "s.bind(('0.0.0.0', 5000))",
        "s.listen(5)",
        "",
        "conn, addr = s.accept()",
        "msg = conn.recv(4096)",
        "conn.sendall(reply + '\\n')",
        "conn.close()     # loop again",
    ]):
        d.text((1112, 282 + i * 33), line, font=mono(19), fill=INK)

    # network zone, kept clear of the two arrows
    rounded(d, (676, 292, 1024, 508), radius=22, fill=PANEL, outline=BOX_EDGE, width=2)
    d.text((742, 312), "TCP  /  IPv4", font=bold(24), fill=INK)
    d.text((716, 352), "byte stream; the newline", font=mono(17), fill=MUTED)
    d.text((716, 376), "character marks messages", font=mono(17), fill=MUTED)
    d.text((716, 424), "port 5000", font=bold(20), fill=ACCENT)
    d.text((716, 454), "127.0.0.1 or LAN IP", font=mono(17), fill=MUTED)

    # request arrows above and below the network panel
    arrow(d, (622, 240), (1078, 240))
    d.text((706, 200), "1   request message", font=regular(20), fill=GREEN)
    arrow(d, (1078, 570), (622, 570), color=GREEN)
    d.text((706, 588), "2   'Message received'", font=regular(20), fill=GREEN)

    d.text((60, 716), "AF_INET + SOCK_STREAM = IPv4 / TCP.  The listening socket "
                      "never closes: accept() returns a new socket for each client.",
           font=regular(20), fill=MUTED)
    d.text((60, 748), "Every message ends with '\\n', so one recv() call is never "
                      "mistaken for a whole message.",
           font=regular(20), fill=MUTED)

    out = SHOTS / "fig_arch.png"
    img.save(out)
    print("wrote", out)


# ---------------------------------------------------------------------------
# Figure: sequence of one request / reply
# ---------------------------------------------------------------------------
def sequence():
    W, H = 1700, 1040
    img = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(img)

    d.text((60, 40), "Message sequence of one request / reply",
           font=bold(34), fill=INK)
    d.text((60, 88), "Numbers match the comments in the source code; time flows "
                     "downwards.", font=regular(22), fill=MUTED)

    cx, sx = 430, 1290
    head_top, head_bottom = 190, 262
    bottom = 940

    for x, name, sub in ((cx, "CLIENT", "client.py"),
                         (sx, "SERVER", "server.py")):
        rounded(d, (x - 140, head_top, x + 140, head_bottom), fill=ACCENT_SOFT)
        w = d.textlength(name, font=bold(24))
        d.text((x - w / 2, head_top + 14), name, font=bold(24), fill=ACCENT)
        w = d.textlength(sub, font=mono(17))
        d.text((x - w / 2, head_top + 44), sub, font=mono(17), fill=MUTED)
        dotted_vline(d, x, head_bottom + 6, bottom)

    def label(x, y, text, sub=None, right=False):
        def place(txt, yy, fnt, colour):
            w = d.textlength(txt, font=fnt)
            d.text((x - w if right else x, yy), txt, font=fnt, fill=colour)
        place(text, y, mono(19), INK)
        if sub:
            place(sub, y + 27, regular(17), MUTED)

    def self_mark(x, y):
        d.arc((x - 32, y - 22, x + 32, y + 22), 300, 240, fill=ACCENT, width=3)

    # 1  socket()
    self_mark(cx, 330)
    label(cx + 50, 306, "1. socket(AF_INET, SOCK_STREAM)",
          "creates an endpoint, no traffic yet")

    # 2  connect()
    arrow(d, (cx + 8, 420), (sx - 8, 420))
    label(cx + 50, 368, "2. connect((host, 5000))", "TCP three-way handshake")

    # 3  accept()
    self_mark(sx, 510)
    label(sx - 40, 486, "3. accept() -> conn, addr", "blocks until a client arrives",
          right=True)

    # 4  message
    arrow(d, (cx + 8, 600), (sx - 8, 600))
    label(cx + 50, 548, "4. sendall(message + '\\n')", "newline = message boundary")

    # 5  receive + print
    label(sx - 40, 690, "5. recv() -> message", "printed on the server terminal",
          right=True)

    # 6  confirmation
    arrow(d, (sx - 8, 780), (cx + 8, 780), color=GREEN)
    label(cx + 50, 728, "6. sendall('Message received' + '\\n')")

    # 7  print the answer
    label(cx + 50, 862, "7. recv() -> reply", "printed as  Server > ...")

    # 8  close
    self_mark(sx, 910)
    label(sx - 40, 886, "8. close(conn)", "loop back to accept() for the next client",
          right=True)

    d.text((60, 980), "Blue = client to server, green = server to client.  "
                      "recv() loops until the '\\n' delimiter arrives.",
           font=regular(20), fill=MUTED)

    out = SHOTS / "fig_sequence.png"
    img.save(out)
    print("wrote", out)


if __name__ == "__main__":
    architecture()
    sequence()
