# Uncomment this to pass the first stage
import re
import socket
import threading


def parse_headers(request_data):
    headers = {}
    header_lines = request_data.split('\r\n')[1:]  # Skip the request line
    for line in header_lines:
        if line:
            key, value = line.split(': ', 1)
            headers[key.lower()] = value
    return headers


def handle_request(client_socket):
    """ Handle a single HTTP request. This function should parse the request, perform any necessary actions, and send a response."""
    try:
        request_data = client_socket.recv(1024).decode("utf-8") # Receive the request data from the client, recv() returns a bytes object, so decode it to a string
        print(request_data) # Print the request data to the console for debugging purposes
        request_lines = request_data.split("\r\n") # Split the request data into lines, they came in as \r\n separated strings which is CRLF (Carriage Return Line Feed) in ASCII

        #Parse the URL path from the request line
        request_line = request_lines[0]
        request_line_parts = request_line.split(" ")
        url_path = request_line_parts[1] # URL path is the second part of the request line, the first part is the method (GET, POST, etc.), and the third part is the HTTP version

        headers = parse_headers(request_data) # Parse the headers from the request data, and store them in a dictionary

        #Check if path matches the /echo/{str} pattern
        echo_match = re.match(r'^/echo/(.+)$', url_path) # Use a regex to match the URL path to the /echo/{str} pattern

        if url_path == "/":
            response = "HTTP/1.1 200 OK\r\n\r\n"
        elif echo_match:
            echo_string = echo_match.group(1)
            content_length = len(echo_string)
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {content_length}\r\n\r\n{echo_string}"
        elif url_path == "/user-agent":
            user_agent = headers.get("user-agent", "")
            content_length = len(user_agent)
            response = f"HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: {content_length}\r\n\r\n{user_agent}"
        else:
            response = "HTTP/1.1 404 Not Found\r\n\r\n"
        client_socket.sendall(response.encode("utf-8"))
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
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

        # enable multiple clients simultaneously
        client_thread = threading.Thread(target=handle_request, args=(client_socket,)) # Create a new thread to handle the client, and pass the client socket to the handle_request function
        client_thread.start()
if __name__ == "__main__":
    main()
