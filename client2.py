import socket
import threading
import sys
SERVER_IP='10.114.206.188'
SERVER_PORT=8888

def receive_messages(sock):
    while True:
        try:
            data=sock.recv(1024)
            if not data:
                print('\n服务器断开了...')
                break
            message=data.decode('utf-8')
            print(f"\r[收到]：{message.strip()}")
            print("你说：",end="",flush=True)
        except Exception as e:
            print(f"接受出错：{e}")
            break

my_name=input('请输入用户名：')
client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
print(f"正在连接{SERVER_IP}:{SERVER_PORT}...")
try:
    client_socket.connect((SERVER_IP,SERVER_PORT))
    print("连接成功！")
    # 启动接收消息的后台线程
    receive_thread = threading.Thread(target=receive_messages, args=(client_socket,), daemon=True)
    receive_thread.start()
except Exception as e:
    print(f"连接失败：{e}")
    sys.exit()


while True:
    msg=input("你说：")
    if msg=='exit':
        break
    data_to_send=f"GROUP|{my_name}|{msg}\n"
    client_socket.sendall(data_to_send.encode('utf-8'))