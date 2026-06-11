import socket
import threading
import sys

def receive(sock):
    try:
        while True:
            data = sock.recv(1024)
            if not data:
                break
            print(data.decode(), end="", flush=True)
    except:
        print("Verbindung verloren")

def main():
    if len(sys.argv) != 3:
        print("Usage: python TcpClient.py <serverIp> <serverPort>")
        return

    server_ip = sys.argv[1]
    server_port = int(sys.argv[2])

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))

    print("Verbunden")
    print("Befehle: send <name> <msg> | clientlist | sendall <msg> | dice invite <name> | dice join | dice decline")

    threading.Thread(target=receive, args=(sock,), daemon=True).start()

    while True:
        try:
            msg = input()
            sock.sendall((msg + "\n").encode())
            if msg.strip() == "exit":
                break
        except:
            break

    sock.close()

if __name__ == "__main__":
    main()
