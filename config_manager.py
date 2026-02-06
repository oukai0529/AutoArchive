import json
import os
import tkinter as tk
from tkinter import simpledialog, messagebox

CONFIG_FILE = "config.json"

# 默认配置模板
DEFAULT_CONFIG = {
    "seven_zip_path": r"C:\Program Files\7-Zip\7z.exe",
    "github_token": "",
    "gist_id": ""
}

def load_config():
    """读取配置，如果不存在或关键信息为空，则弹窗让用户填"""
    config = {}
    
    # 1. 尝试读取现有文件
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            try:
                config = json.load(f)
            except:
                config = DEFAULT_CONFIG.copy()
    else:
        config = DEFAULT_CONFIG.copy()

    # 2. 检查关键信息是否缺失，如果缺失则弹窗询问
    # (这一步是为了让别人下载后，第一次打开能弹出输入框)
    if not config.get("github_token") or not config.get("gist_id"):
        return ask_user_for_info(config)
    
    return config

def ask_user_for_info(current_config):
    """弹窗向导"""
    root = tk.Tk()
    root.withdraw() # 隐藏主窗口，只显示弹窗

    messagebox.showinfo("欢迎", "这是你第一次运行 AutoArchive！\n我们需要配置 GitHub 信息才能作为云数据库。")

    token = simpledialog.askstring("配置向导 (1/2)", "请输入 GitHub Personal Access Token:\n(需要勾选 gist 权限)")
    if not token:
        messagebox.showerror("错误", "必须输入 Token 才能运行！")
        exit()
    
    # 这里的逻辑是：如果是新用户，我们假设他还没有 Gist，
    # 但为了简单，第一步我们先只让他填 Token，
    # 后面 cloud_sync 可以检测到如果没有 ID 就自动创建一个。
    # 这里我们先简单处理：让用户填。如果做成完全自动创建，代码会更多。
    # 为了你现在容易上手，我们先假设用户手动填入 Gist ID。
    gist_id = simpledialog.askstring("配置向导 (2/2)", "请输入你的 Gist ID:\n(如果还没有，请去 gist.github.com 创建一个空的)")
    
    if token and gist_id:
        current_config["github_token"] = token
        current_config["gist_id"] = gist_id
        save_config(current_config)
        return current_config
    else:
        exit()

def save_config(config):
    """保存配置到文件"""
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=4)

def get_7z_path():
    return load_config().get("seven_zip_path", r"C:\Program Files\7-Zip\7z.exe")

def get_token():
    return load_config().get("github_token")

def get_gist_id():
    return load_config().get("gist_id")