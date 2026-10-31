import socket
import threading
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0",8888))
server.listen(5)
clients=[]
clients_lock = threading.Lock()
def broadcast(message,sender):
    with clients_lock:
        targets = clients.copy()

    for c in targets:
        if c == sender:
            continue
        try:
            c.sendall(message.encode("utf-8"))
        except OSError:
            pass
def handle_client(client,address):
    print(f"用户{address}已连接")
    with clients_lock:
        clients.append(client)
    buffer=b""
    while True:
        try:
            data = client.recv(1024)
            if not data:
                break

            buffer+=data

            while b"\n" in buffer:
                line,buffer=buffer.split(b"\n",1)
                text=line.decode("utf-8").strip()

                if text:
                    parts = text.split("|", 2)

                    if len(parts) == 3 and parts[0] == "GROUP":
                        username = parts[1]
                        message = parts[2]

                        print(f"{username}: {message}")
                        broadcast(text + "\n", client)
        except (ConnectionError,OSError):
            break
    with clients_lock:
        if client in clients:
            clients.remove(client)
    client.close()
    print(f"用户{address}已断开")
print("服务器启动成功，等待客户端连接...")

while True:
    client, address = server.accept()

    thread = threading.Thread(
        target=handle_client,
        args=(client, address),
        daemon=True
    )
    thread.start()