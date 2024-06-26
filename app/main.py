# Uncomment this to pass the first stage
import os
import re
import socket
import sys
import threading


def parse_headers(request_data):
    headers = {}
    header_lines = request_data.split('\r\n')[1:]  # Skip the request line
    for line in header_lines:
        if line:
            key, value = line.split(': ', 1)
            headers[key.lower()] = value
    return headers


def handle_request(client_socket, directory):
    try:
        request_data = client_socket.recv(1024).decode("utf-8")
        print(request_data)
        request_lines = request_data.split("\r\n")

        request_line = request_lines[0]
        method, url_path, _ = request_line.split(" ")

        headers = parse_headers(request_data)

        if method == "GET":
            handle_get_request(client_socket, url_path, headers, directory)
        elif method == "POST":
            handle_post_request(client_socket, url_path, headers, directory)
        else:
            response = "HTTP/1.1 405 Method Not Allowed\r\n\r\n"
            client_socket.sendall(response.encode("utf-8"))

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client_socket.close()

def handle_post_request(client_socket, url_path, headers, directory):
    file_match = re.match(r'^/files/(.+)$', url_path)

    if file_match and directory:
        filename = file_match.group(1)
        content_length = int(headers.get('content-length', 0))

        # Read the request body
        body = client_socket.recv(content_length).decode("utf-8")

        file_path = os.path.join(directory, filename)

        # Write the content to the file
        with open(file_path, "w") as file:
            file.write(body)

        response = "HTTP/1.1 201 Created\r\n\r\n"
    else:
        response = "HTTP/1.1 404 Not Found\r\n\r\n"

    client_socket.sendall(response.encode("utf-8"))

def handle_get_request(client_socket, url_path, headers, directory):
    echo_match = re.match(r'^/echo/(.+)$', url_path)
    file_match = re.match(r'^/files/(.+)$', url_path)

    if url_path == "/":
        response = "HTTP/1.1 200 OK\r\n\r\n"
    elif echo_match:
        echo_string = echo_match.group(1)
        content_length = len(echo_string)
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {content_length}\r\n\r\n{echo_string}"
    elif file_match and directory:
        file_name = file_match.group(1)
        file_path = os.path.join(directory, file_name)
        if os.path.exists(file_path):
            with open(file_path, "rb") as file:
                file_content = file.read()
            content_length = len(file_content)
            response = f"HTTP/1.1 200 OK\r\nContent-Type: application/octet-stream\r\nContent-Length: {content_length}\r\n\r\n".encode() + file_content
        else:
            response = "HTTP/1.1 404 Not Found\r\n\r\n"
    elif url_path == "/user-agent":
        user_agent = headers.get("user-agent", "")
        content_length = len(user_agent)
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {content_length}\r\n\r\n{user_agent}"
    else:
        response = "HTTP/1.1 404 Not Found\r\n\r\n"

    if isinstance(response, str):
        response = response.encode("utf-8")
    client_socket.sendall(response)

def main():
    print("Starting xerex server...")
    directory = None
    if len(sys.argv) == 3 and sys.argv[1] == "--directory": # example: python3 main.py --directory /path/to/directory
        directory = sys.argv[2] # /path/to/directory

    server_socket = socket.create_server(("localhost", 4221), reuse_port=True)
    print("Server is running on port 4221!!!")

    if directory:
        print(f"Server is serving from directory: {directory}")
    else:
        print("No directory specified. File serving is disabled.")

    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        client_thread = threading.Thread(target=handle_request, args=(client_socket, directory))
        client_thread.start()

if __name__ == "__main__":
    main()
