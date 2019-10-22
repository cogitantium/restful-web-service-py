import socket
import threading
import http

PRINT_LOCK = threading.Lock()
HOST = ("localhost", 8002)
DATA = dict(first="42")


def thread_print(arg):
    with PRINT_LOCK:
        print(arg)


def http_response(code, body) -> bytes:
    """
    Constructs a HTTP response from a given code and body
    :param code: the HTTP status code to use for the HTTP response line
    :param body: the body to append the HTTP response
    :return: the UTF-8-encoded HTTP-response
    """
    http_status = http.HTTPStatus(code)
    line = f"HTTP/1.0 {code} {http_status.phrase}\r\n\r\n{body}"
    thread_print(f"[SERVER] Sending response: {line}")
    return line.encode("UTF-8")


def handle_client(conn: socket.socket, addr: str):
    """
    Handles a client REST-request to the resource 'data' and implements basic GET, ADD, OVERWRITE, and DELETE operations
    :param conn: the socket representing the client connection
    :param addr: the client address
    :return:
    """
    thread_print(f"[SERVER] Got connection from {addr}")

    # Receive data (up to 512 bytes) and decode
    request = conn.recv(512).decode("UTF-8")

    thread_print(f"[SERVER] Got request: {request}, from: {addr}")

    # HTTP follows the form: 'METHOD-TOKEN REQUEST-URI HTTP-PROTOCOL'
    # Strip potential whitespace for sanity
    request = request.strip()
    method_token = request.split()[0]
    request_uri = request.split()[1]
    # resource should be the second (first) element in path. Note, that the empty element before the first '/' counts.
    resource = request_uri.split('/')[1]
    # Key should be the third (second) element in path
    key = request_uri.split('/')[2]
    # Get body as last element in request FIXME; does not take into account that bodies can be space-separated
    body = request.split()[len(request.split()) - 1]

    # Check if path refers to the resource 'data', if not respond with bad-request to client
    if resource == "data":
        # Process each operation; {GET, PUT, POST, DELETE}, otherwise reply with bad-request to client
        if method_token == "GET":
            try:
                conn.sendall(http_response(200, DATA[key]))
            except KeyError:
                conn.sendall(http_response(404, f"Could not find key: {key}"))
        elif method_token == "PUT":
            if key not in DATA:
                DATA[key] = body
                conn.sendall(http_response(200, f"Set key: {key} = {body}"))
            else:
                conn.sendall(
                    http_response(400, f"Cannot overwrite key: {key} = {body}. Key: {key} already has {DATA[key]}"))
        elif method_token == "POST":
            if key in DATA:
                DATA[key] = body
                conn.sendall(http_response(200, f"Updated key: {key} = {body}"))
            else:
                conn.sendall(http_response(400, f"Cannot overwrite key: {key} = {body}. Key does not exist."))
        elif method_token == "DELETE":
            try:
                del DATA[key]
                conn.sendall(f"HTTP/1.0 200 OK\r\n\r\nSuccessfully deleted key: {key}".encode("UTF-8"))
            except KeyError:
                conn.sendall(f"HTTP/1.0 404 Not Found\r\n\r\nCould not find key for deletion: {key}".encode("UTF-8"))
        else:
            thread_print(f"Bad request. Request: {request} from: {addr}")
            conn.sendall(http_response(400, f"Did not understand method: {method_token}"))
            conn.close()
    else:
        conn.sendall(http_response(400, f"Server does not have the given resource {resource}"))
        conn.close()


def start_server():
    # Declare a socket  on localhost using TCP and IPv4
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Allow rapid restarting of server
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # Bind to HOST-constant
    sock.bind(HOST)

    # Begin listening to socket
    sock.listen()

    # Loop on accepting new connections
    while True:
        thread_print("[SERVER] Accepting incoming connections")
        # Accept a connection, resulting in a tuple, (conn, addr), where conn is the socket representing
        # the client connection and addr is the IP:PORT of the client
        (conn, addr) = sock.accept()
        # Start a thread on the handle_client function, giving the newly accepted client as arguments
        threading.Thread(target=handle_client, args=(conn, addr)).start()


start_server()
