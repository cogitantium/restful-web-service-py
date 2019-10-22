#!/usr/bin/python
import socket
import sys

HOST = ("localhost", 8002)


def send_request(request, body):
    # Declare a socket
    sock = socket.socket()

    # Connect to server
    sock.connect(HOST)

    # Form the request to send
    request = f"{request} HTTP/1.0\r\n\r\n{body}"

    print(f"[CLIENT] Sending request: {request}")

    # Send encoded request to server
    sock.sendall(request.encode("UTF-8"))

    # Receive response from server, decoding and stripping of whitespace
    data = sock.recv(512).decode("UTF-8").strip()

    print(f"[CLIENT] Got reply: {data}")


# Dirty fix for space-separated arguments as one and send request to server.
if sys.argv.__len__() > 1:
    r_body = input("Input body: ")
    send_request(" ".join(sys.argv[1:]), r_body)
else:
    r_input = input("Input '$method $path': ")
    r_body = input("Input body: ")

    send_request(r_input, r_body)
