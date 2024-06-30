import asyncio
import argparse
import re
import sys
from asyncio.streams import StreamReader, StreamWriter
from pathlib import Path
import gzip
import base64

CONFIGURATION = {}

def log_error(*args, **kwargs):
    print(*args, **kwargs, file=sys.stderr)

def extract_request_data(content: bytes) -> tuple[str, str, dict[str, str], str]:
    lines = content.split(b"\r\n")
    request_line = lines[0]
    method, path, _ = request_line.split(b" ")

    headers = {}
    body_start = 0
    for i, line in enumerate(lines[1:], 1):
        if line == b"":
            body_start = i + 1
            break
        key, value = line.split(b": ")
        headers[key.decode()] = value.decode()

    body = b"".join(lines[body_start:]).decode()
    return method.decode(), path.decode(), headers, body

def create_response(
        status: int,
        headers: dict[str, str] | None = None,
        content: str | bytes = "",
) -> bytes:
    headers = headers or {}
    status_messages = {
        200: "OK",
        201: "Created",
        404: "Not Found",
    }

    if isinstance(content, str):
        content = content.encode()

    response_lines = [
        f"HTTP/1.1 {status} {status_messages[status]}",
        *[f"{k}: {v}" for k, v in headers.items()],
        f"Content-Length: {len(content)}",
        "",
    ]

    return b"\r\n".join(line.encode() for line in response_lines) + b"\r\n" + content



async def process_request(reader: StreamReader, writer: StreamWriter) -> None:
    method, path, headers, body = extract_request_data(await reader.read(2**16))

    # Check if the client accepts gzip encoding
    accepts_gzip = 'gzip' in headers.get('Accept-Encoding', '').lower()

    if re.fullmatch(r"/", path):
        writer.write(b"HTTP/1.1 200 OK\r\n\r\n")
        log_error(f"[OUT] /")
    elif re.fullmatch(r"/user-agent", path):
        ua = headers["User-Agent"]
        response_headers = {"Content-Type": "text/plain"}
        content = ua
        if accepts_gzip:
            response_headers["Content-Encoding"] = "gzip"
            content = base64.b64encode(gzip.compress(ua.encode())).decode()
        writer.write(create_response(200, response_headers, content))
        log_error(f"[OUT] user-agent {ua}")
    elif match := re.fullmatch(r"/echo/(.+)", path):
        msg = match.group(1)
        response_headers = {"Content-Type": "text/plain"}
        content = msg
        if accepts_gzip:
            response_headers["Content-Encoding"] = "gzip"
            content = base64.b64encode(gzip.compress(msg.encode())).decode()
        writer.write(create_response(200, response_headers, content))
        log_error(f"[OUT] echo {msg}")
    elif match := re.fullmatch(r"/files/(.+)", path):
        file_path = Path(CONFIGURATION["DIR"]) / match.group(1)

        if method.upper() == "GET" and file_path.is_file():
            content = file_path.read_text()
            response_headers = {"Content-Type": "application/octet-stream"}
            if accepts_gzip:
                response_headers["Content-Encoding"] = "gzip"
                content = base64.b64encode(gzip.compress(content.encode())).decode()
            writer.write(create_response(200, response_headers, content))
        elif method.upper() == "POST":
            file_path.write_bytes(body.encode())
            writer.write(create_response(201))
        else:
            writer.write(create_response(404))
        log_error(f"[OUT] file {path}")
    else:
        writer.write(create_response(404, {}, ""))
        log_error(f"[OUT] 404")

    writer.close()

async def run_server():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("--directory", default=".")
    args = arg_parser.parse_args()
    CONFIGURATION["DIR"] = args.directory

    server = await asyncio.start_server(process_request, "localhost", 4221)

    async with server:
        log_error("Starting server...")
        log_error(f"--directory {CONFIGURATION['DIR']}")
        await server.serve_forever()

if __name__ == "__main__":
    asyncio.run(run_server())
