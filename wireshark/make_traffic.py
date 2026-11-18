"""Replay a fixed HTTP/HTTPS request and check certificate rejection locally."""

import http.client
import ssl
import sys
import tempfile
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lab import BODY, tls_contexts

HTTP_PORT = 18080
TLS_PORT = 18443
REPLY = b"lesson sample received\n"


class LessonHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_POST(self):
        length = self.headers.get("Content-Length")
        if self.path != "/lesson" or length != str(len(BODY)):
            self.send_error(400)
            return
        if self.rfile.read(len(BODY)) != BODY:
            self.send_error(400)
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(REPLY)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(REPLY)

    def version_string(self):
        return "FoxframeLab"

    def log_message(self, format, *args):
        pass


@contextmanager
def listener(port, context=None):
    with HTTPServer(("127.0.0.1", port), LessonHandler) as server:
        if context is not None:
            server.socket = context.wrap_socket(server.socket, server_side=True)
        thread = Thread(target=server.serve_forever)
        thread.start()
        try:
            yield
        finally:
            server.shutdown()
            thread.join()


def send(connection):
    try:
        connection.request(
            "POST",
            "/lesson",
            body=BODY,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        response = connection.getresponse()
        if response.status != 200 or response.read() != REPLY:
            raise RuntimeError("Unexpected workshop response")
        print(f"{connection.port}: 200 OK")
    finally:
        connection.close()


def main():
    if not ssl.HAS_TLSv1_3:
        raise SystemExit("This example needs Python with TLS 1.3 support.")
    with tempfile.TemporaryDirectory(prefix="wifi-pcap-") as temp:
        server_context, trusted_context = tls_contexts(Path(temp))
        with listener(HTTP_PORT), listener(TLS_PORT, server_context):
            send(http.client.HTTPConnection("127.0.0.1", HTTP_PORT, timeout=5))
            send(http.client.HTTPSConnection("localhost", TLS_PORT, context=trusted_context, timeout=5))
            untrusted = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            try:
                send(http.client.HTTPSConnection("localhost", TLS_PORT, context=untrusted, timeout=5))
            except ssl.SSLCertVerificationError as error:
                print(f"{TLS_PORT}: certificate verification rejected ({error.verify_message})")
            else:
                raise RuntimeError("Unexpectedly accepted the untrusted certificate")


if __name__ == "__main__":
    main()
