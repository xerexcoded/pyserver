# Uncomment this to pass the first stage
import socket


def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!")

    # Uncomment this to pass the first stage
    #
    server_socket = socket.create_server(("localhost", 4221), reuse_port=True) # reuse_port=True is needed for multiple clients
    # server_socket.accept() # wait for client
    server_socket.accept()[0].sendall(b"HTTP/1.1 200 OK\r\n\r\n") # send data to client, by accepting the connection and sending data

if __name__ == "__main__":
    main()
