import socket
import threading

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("0.0.0.0", 8888))
server.listen(5)

clients = []
clients_lock = threading.Lock()
users = {}

def send_user_list():
    with clients_lock:
        names = list(users.keys())
        targets = list(users.values())
    message = "USERS|" + "|".join(names) + "\n"
    for c in set(targets):
        try:
            c.sendall(message.encode("utf-8"))
        except OSError:
            pass

def broadcast(message, sender):
    with clients_lock:
        targets = clients.copy()
    for c in targets:
        if c == sender:
            continue
        try:
            c.sendall(message.encode("utf-8"))
        except OSError:
            pass

def handle_client(client, address):
    print(f"用户{address}已连接")
    with clients_lock:
        clients.append(client)
    logged_in_user = None
    buffer = b""
    while True:
        try:
            data = client.recv(1024)
            if not data:
                break
            buffer += data
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                text = line.decode("utf-8").strip()
                if text:
                    parts = text.split("|", 3)
                    if len(parts) == 2 and parts[0] == "LOGIN":
                        username = parts[1]
                        if logged_in_user is not None:
                            client.sendall("ERROR|请勿重复登录\n".encode("utf-8"))
                            continue
                        with clients_lock:
                            if username in users:
                                duplicate = True
                            else:
                                users[username] = client
                                duplicate = False
                        if duplicate:
                            client.sendall("ERROR|用户名已被占用\n".encode("utf-8"))
                            raise ConnectionError("用户名重复")
                        logged_in_user = username
                        print(f"{username} 已上线！")
                        send_user_list()
                    elif len(parts) == 3 and parts[0] == "GROUP":
                        username = parts[1]
                        message = parts[2]
                        if logged_in_user != username:
                            client.sendall("ERROR|用户名不匹配\n".encode("utf-8"))
                            continue
                        print(f"{username}: {message}")
                        broadcast(text + "\n", client)
                    elif len(parts) == 4 and parts[0] == "PRIVATE":
                        sender = parts[1]
                        receiver = parts[2]
                        message = parts[3]
                        if logged_in_user != sender:
                            client.sendall("ERROR|用户名不匹配\n".encode("utf-8"))
                            continue
                        with clients_lock:
                            target = users.get(receiver)
                        if target:
                            target.sendall(f"PRIVATE|{sender}|{message}\n".encode("utf-8"))
                        else:
                            client.sendall(f"ERROR|用户{receiver}不在线\n".encode("utf-8"))
        except (ConnectionError, OSError):
            break
    with clients_lock:
        if client in clients:
            clients.remove(client)
        for name, conn in list(users.items()):
            if conn is client:
                del users[name]
    client.close()
    print(f"用户{address}已断开")
    if logged_in_user:
        broadcast(f"NOTICE|{logged_in_user}已下线\n", client)
    send_user_list()

print("服务器启动成功，等待客户端连接...")
while True:
    client, address = server.accept()
    thread = threading.Thread(target=handle_client, args=(client, address), daemon=True)
    thread.start()
