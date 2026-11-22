"""Loopback SMTP inbox for local development."""

import argparse
import asyncio
import ssl
from pathlib import Path
from uuid import uuid4

import trustme
from aiosmtpd.smtp import SMTP


class Capture:
    def __init__(self, inbox: Path):
        self.inbox = inbox

    async def handle_DATA(self, server, session, envelope):
        message = self.inbox / f"{uuid4().hex}.eml"
        message.write_bytes(envelope.original_content)
        print(f"Captured {message.name}", flush=True)
        return "250 captured"


async def serve(state_dir: Path, port: int) -> None:
    inbox = state_dir / "inbox"
    inbox.mkdir(parents=True, exist_ok=True)
    ca = trustme.CA()
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    ca.issue_cert("127.0.0.1").configure_cert(context)
    ca.cert_pem.write_to_path(state_dir / "smtp-ca.pem")
    server = await asyncio.get_running_loop().create_server(
        lambda: SMTP(Capture(inbox)), "127.0.0.1", port, ssl=context
    )
    async with server:
        print(f"Local SMTP listening on 127.0.0.1:{port}", flush=True)
        await server.serve_forever()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--state-dir", type=Path, required=True)
    parser.add_argument("--port", type=int, default=1465)
    args = parser.parse_args()
    try:
        asyncio.run(serve(args.state_dir, args.port))
    except KeyboardInterrupt:
        pass
