import sys
import os
import threading
import tkinter as tk
from tkinter import scrolledtext, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD

# 引入我们之前写好的逻辑
import packer
import unpacker

class ArchiveApp:
    def __init__(self, root):
        self.root = root
        self.root.title("My Auto Archive (IC Engineer Edition)")
        self.root.geometry("600x450")
        
        # 1. 顶部提示区
        self.label = tk.Label(
            root, 
            text="⬇️ 请将 [文件夹] 或 [.7z压缩包] 拖入下方区域 ⬇️", 
            font=("微软雅黑", 12, "bold"),
            pady=10
        )
        self.label.pack()

        # 2. 核心拖拽区域 (用一个只读的文本框充当)
        self.drop_area = tk.Label(
            root,
            text="[ 拖拽感应区 ]\n\n把文件扔进来\n自动识别 打包/解压",
            bg="#f0f0f0",
            relief="groove",
            width=60,
            height=6
        )
        self.drop_area.pack(pady=10, padx=20, fill="x")

        # 注册拖拽功能
        self.drop_area.drop_target_register(DND_FILES)
        self.drop_area.dnd_bind('<<Drop>>', self.on_drop)

        # 3. 日志输出窗口
        self.log_window = scrolledtext.ScrolledText(root, height=12, state='disabled', bg="#1e1e1e", fg="#00ff00", font=("Consolas", 10))
        self.log_window.pack(pady=10, padx=10, fill="both", expand=True)

        # === 黑魔法：重定向 print 输出到 GUI ===
        # 这样 packer.py 里的 print 就会自动显示到窗口里，不用改原来的代码
        sys.stdout = self
        sys.stderr = self

    def write(self, text):
        """捕获 print 的内容并显示在日志窗口"""
        self.log_window.config(state='normal') # 解锁
        self.log_window.insert(tk.END, text)
        self.log_window.see(tk.END)            # 自动滚动到底部
        self.log_window.config(state='disabled') # 锁定
        # 强制刷新界面，防止卡顿
        self.root.update_idletasks()

    def flush(self):
        pass

    def on_drop(self, event):
        """当文件被拖入时触发"""
        # event.data 返回的路径在大括号里（如果是带空格的路径），需要清洗一下
        file_paths = event.data
        if file_paths.startswith('{') and file_paths.endswith('}'):
            file_paths = file_paths[1:-1]
        
        self.log(f"\n🚀 检测到拖入: {file_paths}")
        
        # 开启一个新线程来处理，防止界面卡死
        threading.Thread(target=self.process_logic, args=(file_paths,), daemon=True).start()

    def process_logic(self, path):
        """判断是打包还是解包"""
        path = path.strip() # 去除可能多余的空格
        
        if not os.path.exists(path):
            self.log("❌ 错误：路径不存在")
            return

        if os.path.isdir(path):
            self.log("📂 识别为文件夹 -> 准备 [打包]...")
            try:
                packer.archive_folder(path)
            except Exception as e:
                self.log(f"❌ 打包出错: {e}")
                
        elif os.path.isfile(path) and path.endswith('.7z'):
            self.log("📦 识别为压缩包 -> 准备 [解压]...")
            try:
                unpacker.unpack_archive(path)
            except Exception as e:
                self.log(f"❌ 解压出错: {e}")
        else:
            self.log("⚠️ 无法识别的文件类型！请拖入文件夹或 .7z 文件。")

    def log(self, message):
        print(message)

# 启动程序
if __name__ == "__main__":
    # 注意：这里用的是 TkinterDnD.Tk 而不是普通的 tk.Tk
    root = TkinterDnD.Tk()
    app = ArchiveApp(root)
    root.mainloop()