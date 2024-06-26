# Uncomment this to pass the first stage
import re
import socket

def handle_request(client_socket):
    request_data = client_socket.recv(1024).decode("utf-8")
    request_lines = request_data.split("\r\n") # Split the request data into lines, they came in as \r\n separated strings which is CRLF (Carriage Return Line Feed) in ASCII

    #Parse the URL path from the request line
    request_line = request_lines[0]
    request_line_parts = request_line.split(" ")
    url_path = request_line_parts[1] # URL path is the second part of the request line, the first part is the method (GET, POST, etc.), and the third part is the HTTP version

    #Check if path matches the /echo/{str} pattern
    echo_match = re.match(r'^/echo/(.+)$', url_path)

    if url_path == "/":
        response = "HTTP/1.1 200 OK\r\n\r\n"
    elif echo_match:
        echo_string = echo_match.group(1)
        content_length = len(echo_string)
        response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {content_length}\r\n\r\n{echo_string}"
    else:
        response = "HTTP/1.1 404 Not Found\r\n\r\n"
    client_socket.sendall(response.encode("utf-8"))
    client_socket.close()

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True) # reuse_port=True is needed for multiple clients
    # server_socket.accept() # wait for client
    # server_socket.accept()[0].sendall(b"HTTP/1.1 200 OK\r\n\r\n") # send data to client, by accepting the connection and sending data
    print("Server is running on port 4221!!!")
    while True:
        client_socket, addr = server_socket.accept()
        print(f"Connection from {addr}")
        handle_request(client_socket)
if __name__ == "__main__":
    main()
