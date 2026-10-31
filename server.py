import socket
import threading
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0",8888))
server.listen(5)
clients=[]
clients_lock = threading.Lock()
users={}
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
                    parts = text.split("|", 3)

                    if len(parts) == 2 and parts[0] == "LOGIN":
                        username = parts[1]

                        with clients_lock:
                            users[username] = client

                        print(f"{username} 已上线！")

                    elif len(parts) == 3 and parts[0] == "GROUP":
                        username = parts[1]
                        message = parts[2]
                        with clients_lock:
                            users[username]=client

                        print(f"{username}: {message}")
                        broadcast(text + "\n", client)
                    elif len(parts) == 4 and parts[0] == "PRIVATE":
                        sender = parts[1]
                        receiver = parts[2]
                        message = parts[3]

                        with clients_lock:
                            target = users.get(receiver)

                        if target:
                            target.sendall(
                                f"PRIVATE|{sender}|{message}\n".encode("utf-8")
                            )
                        else:
                            client.sendall(
                                f"ERROR|用户{receiver}不在线\n".encode("utf-8")
                            )
        except (ConnectionError,OSError):
            break
    with clients_lock:
        if client in clients:
            clients.remove(client)

        for name, conn in list(users.items()):
            if conn is client:
                del users[name]
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
