import asyncio
import argparse
import re
import sys
from asyncio.streams import StreamReader, StreamWriter
from pathlib import Path

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
        content: str = "",
) -> bytes:
    headers = headers or {}
    status_messages = {
        200: "OK",
        201: "Created",
        404: "Not Found",
    }

    response_lines = [
        f"HTTP/1.1 {status} {status_messages[status]}",
        *[f"{k}: {v}" for k, v in headers.items()],
        f"Content-Length: {len(content)}",
        "",
        content,
    ]

    return b"\r\n".join(line.encode() for line in response_lines)

async def process_request(reader: StreamReader, writer: StreamWriter) -> None:
    method, path, headers, body = extract_request_data(await reader.read(2**16))

    if re.fullmatch(r"/", path):
        writer.write(b"HTTP/1.1 200 OK\r\n\r\n")
        log_error(f"[OUT] /")
    elif re.fullmatch(r"/user-agent", path):
        ua = headers["User-Agent"]
        writer.write(create_response(200, {"Content-Type": "text/plain"}, ua))
        log_error(f"[OUT] user-agent {ua}")
    elif match := re.fullmatch(r"/echo/(.+)", path):
        msg = match.group(1)
        writer.write(create_response(200, {"Content-Type": "text/plain"}, msg))
        log_error(f"[OUT] echo {msg}")
    elif match := re.fullmatch(r"/files/(.+)", path):
        file_path = Path(CONFIGURATION["DIR"]) / match.group(1)

        if method.upper() == "GET" and file_path.is_file():
            writer.write(
                create_response(
                    200,
                    {"Content-Type": "application/octet-stream"},
                    file_path.read_text(),
                )
            )
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
