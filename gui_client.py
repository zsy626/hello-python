import socket
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox

client_socket = None
my_name = ''
is_connected = False
SERVER_IP = '10.114.206.188'
SERVER_PORT = 8888

def connect_server():
    global client_socket, my_name, is_connected
    my_name = name_entry.get().strip()
    if not my_name:
        messagebox.showwarning("提示", "请输入昵称！")
        return
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect((SERVER_IP, SERVER_PORT))
        is_connected = True
        login_msg = f"LOGIN|{my_name}\n"
        client_socket.sendall(login_msg.encode("utf-8"))
        receive_thread = threading.Thread(target=receive_message, args=(client_socket,), daemon=True)
        receive_thread.start()
        connect_btn.config(state='disabled')
        send_btn.config(state='normal')
        name_entry.config(state='disabled')
        chat_display.config(state='normal')
        chat_display.insert(tk.END, f"[系统]连接成功！欢迎{my_name}进入聊天室。\n")
        chat_display.config(state='disabled')
    except Exception as e:
        messagebox.showerror("连接失败", f"无法连接服务器：{e}")

def update_chat_display(text):
    chat_display.config(state='normal')
    chat_display.insert(tk.END, text)
    chat_display.yview(tk.END)
    chat_display.config(state='disabled')

def handle_disconnect():
    global is_connected
    is_connected = False
    connect_btn.config(state="normal")
    send_btn.config(state="disabled")
    name_entry.config(state="normal")

def receive_message(sock):
    buffer = b""
    while True:
        try:
            data = sock.recv(1024)
            if not data:
                root.after(0, update_chat_display, "\n[系统]服务器断开了...\n")
                root.after(0, handle_disconnect)
                break
            buffer += data
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                message = line.decode('utf-8').strip()
                if not message:
                    continue
                parts = message.split("|")
                if parts[0] == "GROUP" and len(parts) == 3:
                    display_text = f"[{parts[1]}]: {parts[2]}\n"
                elif parts[0] == "PRIVATE" and len(parts) == 3:
                    display_text = f"【私聊】[{parts[1]}]: {parts[2]}\n"
                elif parts[0] == "USERS":
                    display_text = f"[系统] 当前在线：{', '.join(parts[1:])}\n"
                elif parts[0] == "NOTICE" and len(parts) == 2:
                    display_text = f"[系统] {parts[1]}\n"
                elif parts[0] == "ERROR" and len(parts) == 2:
                    display_text = f"[系统]: {parts[1]}\n"
                else:
                    display_text = f"[系统]: {message}\n"
                root.after(0, update_chat_display, display_text)
        except Exception as e:
            root.after(0, update_chat_display, f"[系统]连接异常：{e}\n")
            root.after(0, handle_disconnect)
            break

def send_message(event=None):
    global client_socket, my_name, is_connected
    if not is_connected:
        return
    msg = msg_entry.get().strip()
    if not msg:
        return
    try:
        if msg.startswith("@"):
            parts = msg[1:].split(" ", 1)
            if len(parts) != 2:
                messagebox.showwarning("格式错误", "私聊格式：@用户名 消息")
                return
            receiver, content = parts
            data_to_send = f"PRIVATE|{my_name}|{receiver}|{content}\n"
            update_chat_display(f"我(私聊给{receiver}): {content}\n")
        else:
            data_to_send = f"GROUP|{my_name}|{msg}\n"
            update_chat_display(f"我({my_name}): {msg}\n")
        client_socket.sendall(data_to_send.encode('utf-8'))
        msg_entry.delete(0, tk.END)
    except Exception as e:
        messagebox.showerror("发送失败", f"网络错误:\n{e}")

root = tk.Tk()
root.title("网络聊天室 - 客户端")
root.geometry("500x600")
top_frame = tk.Frame(root)
top_frame.pack(pady=10)
tk.Label(top_frame, text="昵称:").pack(side=tk.LEFT)
name_entry = tk.Entry(top_frame, width=10)
name_entry.pack(side=tk.LEFT, padx=5)
connect_btn = tk.Button(top_frame, text="连接服务器", command=connect_server)
connect_btn.pack(side=tk.LEFT, padx=10)
chat_display = scrolledtext.ScrolledText(root, width=60, height=20, state='disabled')
chat_display.pack(pady=10)
bottom_frame = tk.Frame(root)
bottom_frame.pack(pady=10, fill=tk.X, padx=10)
msg_entry = tk.Entry(bottom_frame)
msg_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
msg_entry.bind("<Return>", send_message)
send_btn = tk.Button(bottom_frame, text="发送", state='disabled', command=send_message)
send_btn.pack(side=tk.RIGHT)
root.mainloop()
