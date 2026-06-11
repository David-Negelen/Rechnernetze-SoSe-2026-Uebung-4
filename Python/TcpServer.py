import socket
import threading
import random

# =========================================================
# CLIENT HANDLER
# =========================================================

class ClientHandler:

    def __init__(self, name, conn):
        self.name = name
        self.conn = conn


# =========================================================
# STATE
# =========================================================

clients = {}
pending_invites = {}  # inviter_name -> target_name


# =========================================================
# HELPERS
# =========================================================

def broadcast(message, exclude=None):
    for name, client in list(clients.items()):
        if name != exclude:
            try:
                client.conn.sendall(message.encode())
            except:
                pass


# =========================================================
# CLIENT THREAD
# =========================================================

def handle_client(conn):

    name = None

    try:

        # =====================================================
        # REGISTRIERUNG
        # =====================================================

        while True:

            conn.sendall(b"register <name>\n")

            reg = conn.recv(1024).decode().strip()

            if not reg:
                conn.close()
                return

            parts = reg.split(" ")

            if len(parts) != 2 or parts[0].lower() != "register":
                conn.sendall(b"Erwartet: register <name>\n")
                continue

            name = parts[1]

            if name in clients:
                conn.sendall(b"Name bereits vergeben!\n")
                continue

            break

        # =====================================================
        # CLIENT REGISTRIEREN
        # =====================================================

        clients[name] = ClientHandler(name, conn)
        conn.sendall(b"Willkommen!\n")
        print(f"{name} connected")

        # d) Alle anderen benachrichtigen
        broadcast(f"[Server] {name} hat sich verbunden.\n", exclude=name)

        # =====================================================
        # MESSAGE LOOP
        # =====================================================

        while True:

            data = conn.recv(1024)

            if not data:
                break

            msg = data.decode().strip()

            print(f"{name}: {msg}")

            # =================================================
            # SEND
            # =================================================

            if msg.startswith("send "):

                parts = msg.split(" ", 2)

                if len(parts) == 3:
                    target, text = parts[1], parts[2]
                    if target in clients:
                        clients[target].conn.sendall(f"{name}: {text}\n".encode())
                    else:
                        conn.sendall(f"[Server] {target} nicht gefunden.\n".encode())

            # =================================================
            # CLIENTLIST
            # =================================================

            elif msg == "clientlist":

                names = ", ".join(clients.keys()) if clients else "Keine Clients"
                conn.sendall(f"[Clients] {names}\n".encode())

            # =================================================
            # SENDALL
            # =================================================

            elif msg.startswith("sendall "):

                text = msg[8:]
                broadcast(f"{name}: {text}\n", exclude=name)

            # =================================================
            # DICE INVITE
            # =================================================

            elif msg.startswith("dice invite "):

                target = msg[12:].strip()

                if target not in clients:
                    conn.sendall(f"[Server] {target} nicht gefunden.\n".encode())
                elif target == name:
                    conn.sendall(b"[Server] Du kannst dich nicht selbst einladen.\n")
                elif name in pending_invites:
                    conn.sendall(b"[Server] Du hast bereits eine ausstehende Einladung.\n")
                else:
                    pending_invites[name] = target
                    clients[target].conn.sendall(
                        f"[Server] {name} laedt dich zum Wuerfelspiel ein. "
                        f"Antworte mit 'dice join' oder 'dice decline'.\n".encode()
                    )
                    conn.sendall(f"[Server] Einladung an {target} gesendet.\n".encode())

            # =================================================
            # DICE JOIN
            # =================================================

            elif msg == "dice join":

                inviter = next((k for k, v in pending_invites.items() if v == name), None)

                if inviter is None:
                    conn.sendall(b"[Server] Keine ausstehende Einladung.\n")
                elif inviter not in clients:
                    conn.sendall(b"[Server] Einladender Client nicht mehr verbunden.\n")
                    pending_invites.pop(inviter, None)
                else:
                    pending_invites.pop(inviter)

                    rolls = [random.randint(1, 6) for _ in range(4)]
                    inviter_rolls = rolls[:2]
                    joiner_rolls = rolls[2:]
                    inviter_sum = sum(inviter_rolls)
                    joiner_sum = sum(joiner_rolls)

                    if inviter_sum > joiner_sum:
                        inviter_result, joiner_result = "Gewonnen", "Verloren"
                    elif joiner_sum > inviter_sum:
                        inviter_result, joiner_result = "Verloren", "Gewonnen"
                    else:
                        inviter_result = joiner_result = "Unentschieden"

                    clients[inviter].conn.sendall((
                        f"[Wuerfel] Deine Wuerfe: {inviter_rolls[0]}, {inviter_rolls[1]} "
                        f"(Summe: {inviter_sum})\n"
                        f"[Wuerfel] {name}s Wuerfe: {joiner_rolls[0]}, {joiner_rolls[1]} "
                        f"(Summe: {joiner_sum})\n"
                        f"[Wuerfel] Ergebnis: {inviter_result}\n"
                    ).encode())

                    conn.sendall((
                        f"[Wuerfel] Deine Wuerfe: {joiner_rolls[0]}, {joiner_rolls[1]} "
                        f"(Summe: {joiner_sum})\n"
                        f"[Wuerfel] {inviter}s Wuerfe: {inviter_rolls[0]}, {inviter_rolls[1]} "
                        f"(Summe: {inviter_sum})\n"
                        f"[Wuerfel] Ergebnis: {joiner_result}\n"
                    ).encode())

            # =================================================
            # DICE DECLINE
            # =================================================

            elif msg == "dice decline":

                inviter = next((k for k, v in pending_invites.items() if v == name), None)

                if inviter is None:
                    conn.sendall(b"[Server] Keine ausstehende Einladung.\n")
                else:
                    pending_invites.pop(inviter)
                    if inviter in clients:
                        clients[inviter].conn.sendall(
                            f"[Server] {name} hat die Einladung abgelehnt.\n".encode()
                        )
                    conn.sendall(b"[Server] Einladung abgelehnt.\n")

    except Exception as e:

        print(f"Fehler bei {name}: {e}")

    finally:

        # =====================================================
        # DISCONNECT
        # =====================================================

        if name is not None:

            clients.pop(name, None)

            # Offene Einladungen bereinigen
            pending_invites.pop(name, None)
            for k, v in list(pending_invites.items()):
                if v == name:
                    pending_invites.pop(k)
                    if k in clients:
                        clients[k].conn.sendall(
                            f"[Server] {name} hat die Verbindung getrennt. "
                            f"Spiel abgebrochen.\n".encode()
                        )

            print(f"Removed: {name}")

            # d) Alle anderen benachrichtigen
            broadcast(f"[Server] {name} hat die Verbindung getrennt.\n")

        conn.close()


# =========================================================
# TCP SERVER
# =========================================================

def tcp_server(port=9000):

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("0.0.0.0", port))
    server.listen()

    print(f"TCP Server läuft auf Port {port}")

    while True:

        conn, addr = server.accept()

        threading.Thread(
            target=handle_client,
            args=(conn,)
        ).start()


# =========================================================
# MAIN
# =========================================================

if __name__ == "__main__":
    tcp_server()
