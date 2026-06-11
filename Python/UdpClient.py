import socket
import threading
import sys

# =========================================================
# RECEIVE THREAD
# =========================================================

def receiver(sock):

    while True:

        try:

            data, addr = sock.recvfrom(4096)

            msg = data.decode("utf-8")

            print(f"\nEmpfangen von {addr[0]}:{addr[1]}")
            print(msg)

            print("> ", end="", flush=True)

        except:
            break


# =========================================================
# MAIN
# =========================================================

def main():

    if len(sys.argv) != 3:
        print("Usage: python udp_client.py <name> <port>")
        return

    own_name = sys.argv[1]
    own_port = int(sys.argv[2])

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    sock.bind(("0.0.0.0", own_port))

    print("UDP gestartet:")
    print("Name:", own_name)
    print("Port:", own_port)

    contacts = {}  # name -> (ip, port)

    threading.Thread(
        target=receiver,
        args=(sock,),
        daemon=True
    ).start()

    while True:

        print("> ", end="")

        input_line = input().strip()

        # =====================================================
        # SEND
        # =====================================================

        if input_line.startswith("send "):

            parts = input_line.split(" ", 3)

            if len(parts) != 4:
                print("Usage: send <ip> <port> <message>")
                continue

            ip = parts[1]
            port = int(parts[2])
            message = parts[3]

            sock.sendto(f"{own_name}: {message}".encode("utf-8"), (ip, port))

        # =====================================================
        # REGISTER
        # =====================================================

        elif input_line.startswith("register "):

            parts = input_line.split(" ", 3)

            if len(parts) != 4:
                print("Usage: register <name> <ip> <port>")
                continue

            reg_name, reg_ip, reg_port = parts[1], parts[2], int(parts[3])
            contacts[reg_name] = (reg_ip, reg_port)
            print(f"{reg_name} registriert ({reg_ip}:{reg_port})")

        # =====================================================
        # CLIENTLIST
        # =====================================================

        elif input_line == "clientlist":

            if not contacts:
                print("Keine Clients registriert.")
            else:
                for n, (ip, port) in contacts.items():
                    print(f"{n}: {ip}:{port}")

        # =====================================================
        # SENDALL
        # =====================================================

        elif input_line.startswith("sendall "):

            message = input_line[8:]

            if not contacts:
                print("Keine Clients registriert.")
            else:
                msg = f"{own_name}: {message}".encode("utf-8")
                for n, (ip, port) in contacts.items():
                    sock.sendto(msg, (ip, port))

        # =====================================================
        # EXIT
        # =====================================================

        elif input_line == "exit":

            sock.close()
            break

        # =====================================================
        # HELP
        # =====================================================

        else:

            print("Befehle:")
            print("  send <ip> <port> <message>")
            print("  register <name> <ip> <port>")
            print("  clientlist")
            print("  sendall <message>")
            print("  exit")


if __name__ == "__main__":
    main()
