"""Local classroom UI with a fixed HTTP and TLS experiment."""

import argparse
import json
import re
import socket
import ssl
import subprocess
import tempfile
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

STATIC = Path(__file__).resolve().parent / "static"
BODY = b"alias=fox-student&lesson=wifi-security"
REQUEST = (
    b"POST /lesson HTTP/1.1\r\n"
    b"Host: localhost\r\n"
    b"Content-Type: application/x-www-form-urlencoded\r\n"
    + f"Content-Length: {len(BODY)}\r\n\r\n".encode("ascii")
    + BODY
)


def tls_contexts(folder):
    cert = folder / "localhost.pem"
    key = folder / "localhost.key"
    config = folder / "openssl.cnf"
    config.write_text(
        "[req]\ndistinguished_name=dn\nx509_extensions=ext\nprompt=no\n"
        "[dn]\nCN=localhost\n[ext]\nsubjectAltName=DNS:localhost\n",
        encoding="utf-8",
    )
    subprocess.run(
        [
            "openssl", "req", "-x509", "-newkey", "rsa:2048", "-nodes",
            "-days", "1", "-keyout", str(key), "-out", str(cert),
            "-config", str(config),
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    server = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    server.minimum_version = ssl.TLSVersion.TLSv1_3
    server.load_cert_chain(cert, key)
    trusted = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    trusted.load_verify_locations(cafile=str(cert))
    return server, trusted


def exchange(client_context, server_context, send_request):
    """Exchange real TLS records between two endpoints entirely in memory."""
    client_in, client_out = ssl.MemoryBIO(), ssl.MemoryBIO()
    server_in, server_out = ssl.MemoryBIO(), ssl.MemoryBIO()
    client = client_context.wrap_bio(client_in, client_out, server_hostname="localhost")
    server = server_context.wrap_bio(server_in, server_out, server_side=True)

    for _ in range(12):
        completed = []
        for endpoint, outgoing, incoming in (
            (client, client_out, server_in),
            (server, server_out, client_in),
        ):
            try:
                endpoint.do_handshake()
                completed.append(endpoint)
            except ssl.SSLWantReadError:
                pass
            records = outgoing.read()
            if records:
                incoming.write(records)
        if len(completed) == 2:
            break
    else:
        raise RuntimeError("TLS handshake did not finish")

    if send_request:
        if client.write(REQUEST) != len(REQUEST):
            raise RuntimeError("Incomplete TLS request")
        wire = client_out.read()
        server_in.write(wire)
        if server.read(65536) != REQUEST:
            raise RuntimeError("TLS endpoint received unexpected data")
        return wire, client.version()


def evidence():
    left, right = socket.socketpair()
    with left, right, right.makefile("rb") as receiver:
        left.sendall(REQUEST)
        left.shutdown(socket.SHUT_WR)
        plaintext = receiver.read()

    with tempfile.TemporaryDirectory(prefix="wifi-tls-") as temp:
        server, client = tls_contexts(Path(temp))
        wire, version = exchange(client, server, send_request=True)
        untrusted = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        try:
            exchange(untrusted, server, send_request=False)
        except ssl.SSLCertVerificationError as error:
            rejection = error.verify_message
        else:
            raise RuntimeError("Untrusted certificate unexpectedly passed verification")

    return {
        "http": plaintext.decode("ascii"),
        "httpBodyVisible": BODY in plaintext,
        "tlsBodyVisible": BODY in wire,
        "tlsVersion": version,
        "tlsHex": wire[:72].hex(" ", 1),
        "tlsLength": len(wire),
        "serverReceived": BODY.decode("ascii"),
        "rejection": rejection,
    }


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, result, **kwargs):
        self.result = result
        super().__init__(*args, directory=str(STATIC), **kwargs)

    def do_GET(self):
        if self.path == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return

        if self.path == "/evidence.json":
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Content-Length", str(len(self.result)))
            self.end_headers()
            self.wfile.write(self.result)
            return

        if not re.fullmatch(r"/(?:index\.html|gallery\.html|lab\.(?:css|js)|images/(?:one|two|three)\.jpg)?", self.path):
            self.send_error(404)
            return
        if self.path == "/":
            self.path = "/index.html"
        super().do_GET()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    if not ssl.HAS_TLSv1_3:
        parser.error("Python needs TLS 1.3 support. Try a current Python from python.org or Homebrew.")
    result = json.dumps(evidence()).encode("utf-8")
    with ThreadingHTTPServer(("127.0.0.1", args.port), partial(Handler, result=result)) as server:
        print(f"http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
