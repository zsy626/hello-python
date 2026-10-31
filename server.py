import socket
import threading
import tkinter as tk
from tkinter import scrolledtext,messagebox
#全局变量
client_socket=None
my_name=''
is_connected=False
SERVER_IP = '10.114.206.188'
SERVER_PORT = 8888


#连接服务器
def connect_server():
    global client_socket,my_name,is_connected
    my_name=name_entry.get().strip()
    if not my_name:
        messagebox.showwarning("提示","请输入昵称！")
        return
    try:
        #创建连接
        client_socket=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP,SERVER_PORT))
        is_connected=True
        #LOGIN
        login_msg=f"LOGIN|{my_name}\n"
        client_socket.sendall(login_msg.encode("utf-8"))
        receive_thread = threading.Thread(target=receive_messages, args=(client_socket,), daemon=True)
        receive_thread.start()
        #改变界面状态
        connect_btn.config(state='disabled')#只读不能写
        send_btn.config(state='normal')
        name_entry.config(state='disabled')
        #显示
        chat_display.config(state='normal')
        chat_display.insert(tk.END,f"[系统]连接成功！欢迎{my_name}进入聊天室。\n")
        chat_display.config(state='disabled')
    except Exception as e:
        messagebox.showerror("连接失败",f"无法连接服务器：{e}")
#接收消息
def update_chat_display(text):
    chat_display.config(state='normal')
    chat_display.insert(tk.END,text)
    chat_display.yview(tk.END)
    chat_display.config(state='disabled')
def receive_messages(sock):
    while True:
        try:
            data=sock.recv(1024)
            if not data:
                root.after(0,update_chat_display,"\n[系统]服务器断开了...\n")
                break
            message=data.decode('utf-8').strip()
            parts=message.split("|",2)#切两次
            # 如果是群聊
            if parts[0] == "GROUP" and len(parts) == 3:
                display_text = f"[{parts[1]}]: {parts[2]}\n"
            # 如果是私聊
            elif parts[0] == "PRIVATE" and len(parts) == 3:
                display_text = f"【私聊】[{parts[1]}]: {parts[2]}\n"
            # 如果服务器发来错误提示
            elif parts[0] == "ERROR" and len(parts) == 2:
                display_text = f"[系统]: {parts[1]}\n"
            # 其他没见过的格式
            else:
                display_text = f"[系统]: {message}\n"
            root.after(0, update_chat_display, display_text)
        except Exception as e:
            break
        pass


# 发送信息
def send_message(event=None):
    global client_socket, my_name, is_connected

    # 1. 如果没连上服务器，或者没打字，直接返回，不执行
    if not is_connected:
        return
    msg = msg_entry.get().strip()
    if not msg:
        return

    try:
        # 2. 判断是不是私聊（以 @ 开头）
        if msg.startswith("@"):
            # 切分：@用户名 消息内容
            parts = msg[1:].split(" ", 1)
            if len(parts) != 2:
                messagebox.showwarning("格式错误", "私聊格式：@用户名 消息")
                return

            receiver, content = parts
            # 拼装私聊协议
            data_to_send = f"PRIVATE|{my_name}|{receiver}|{content}\n"

            # 界面上显示自己发的私聊（本地回显）
            update_chat_display(f"我(私聊给{receiver}): {content}\n")

        # 3. 否则就是群聊
        else:
            # 拼装群聊协议
            data_to_send = f"GROUP|{my_name}|{msg}\n"

            # 界面上显示自己发的群聊（本地回显）
            update_chat_display(f"我({my_name}): {msg}\n")

        # 4. 发送给服务器
        client_socket.sendall(data_to_send.encode('utf-8'))

        # 5. 发送完毕，清空输入框，方便打下一句
        msg_entry.delete(0, tk.END)

    except Exception as e:
        messagebox.showerror("发送失败", f"网络错误:\n{e}")

# 1. 创建主窗口
root = tk.Tk()
root.title("网络聊天室 - 客户端")
root.geometry("500x600") # 设置窗口大小

# ================= 顶部：连接配置区 =================
top_frame = tk.Frame(root)
top_frame.pack(pady=10)

tk.Label(top_frame, text="昵称:").pack(side=tk.LEFT)
name_entry = tk.Entry(top_frame, width=10)
name_entry.pack(side=tk.LEFT, padx=5)

connect_btn = tk.Button(top_frame, text="连接服务器",command=connect_server)
connect_btn.pack(side=tk.LEFT, padx=10)

# ================= 中部：聊天显示区 =================
# scrolledtext 是一个自带滚动条的文本框
chat_display = scrolledtext.ScrolledText(root, width=60, height=20, state='disabled')
chat_display.pack(pady=10)

# ================= 底部：输入和发送区 =================
bottom_frame = tk.Frame(root)
bottom_frame.pack(pady=10, fill=tk.X, padx=10)

msg_entry = tk.Entry(bottom_frame)
msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
msg_entry.bind("<Return>", send_message)
send_btn = tk.Button(bottom_frame, text="发送", state='disabled',command=send_message) # 默认禁用，连上服务器才能点
send_btn.pack(side=tk.RIGHT)



# 运行主循环
root.mainloop()
