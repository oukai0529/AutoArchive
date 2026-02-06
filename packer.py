import os
import subprocess
import secrets
import string
import hashlib
import json
import time
import cloud_sync
import config_manager # <--- 引入新管家

# ================= 配置区域 =================
# 动态获取 7z 路径
SEVEN_ZIP_PATH = config_manager.get_7z_path()

# 压缩包存放的目录
OUTPUT_DIR = "output_archives"
# 密码本存放路径
DB_FILE = "local_keys_db.json"
# ===========================================

# ... (后面的代码不用动)

def generate_password(length=16):
    """生成一个高强度的随机密码"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for i in range(length))

def calculate_file_hash(filepath):
    """计算文件的 MD5 校验码（用于后续验证身份）"""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def archive_folder(source_path):
    """核心逻辑：压缩文件夹"""
    
    # 1. 准备路径和名称
    if not os.path.exists(source_path):
        print(f"❌ 错误：找不到文件夹 {source_path}")
        return

    # 确保输出目录存在
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    folder_name = os.path.basename(source_path.strip(os.sep))
    # 为了防止文件名泄露内容，我们用时间戳+随机字符重命名压缩包
    # 比如：archive_20240101_xh8s.7z
    timestamp = int(time.time())
    random_suffix = secrets.token_hex(2)
    archive_name = f"archive_{timestamp}_{random_suffix}.7z"
    output_path = os.path.join(OUTPUT_DIR, archive_name)

    # 2. 生成密码
    password = generate_password()
    print(f"🔑 生成随机密码: {password}")

    # 3. 调用 7-Zip 进行加密压缩
    # 7z 命令参数解释：
    # a: 添加到压缩包
    # -p: 密码
    # -mhe=on: 开启头部加密（Hide Headers），这样别人连文件名都看不到，只能看到乱码
    # -mx=0: 压缩等级（0是仅存储不压缩，速度最快；5是正常；9是最大压缩）。
    #        如果你存视频，建议用 -mx=0，因为视频很难再压缩，这样速度极快。
    print(f"📦 正在打包 {folder_name} ...")
    
    cmd = [
        SEVEN_ZIP_PATH, 
        'a', 
        output_path, 
        source_path, 
        f'-p{password}', 
        '-mhe=on',
        '-mx=0' 
    ]

    try:
        # 运行命令行，capture_output=True 可以捕获 7zip 的输出，不让他刷屏
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ 7-Zip 报错了：")
            print(result.stderr)
            return
        
        print(f"✅ 打包成功！文件位于: {output_path}")

    except FileNotFoundError:
        print("❌ 错误：找不到 7z.exe，请检查代码顶部的 SEVEN_ZIP_PATH 配置！")
        return

    # 4. 计算生成文件的哈希值 (模拟生成指纹)
    print("🔍 正在计算文件指纹(MD5)...")
    file_hash = calculate_file_hash(output_path)
    print(f"🏷️ 文件指纹: {file_hash}")

    # 5. 保存到本地数据库 (JSON)
    save_record(folder_name, archive_name, file_hash, password)

def save_record(original_name, archive_name, md5, password):
    """将记录同时保存到 GitHub 和 本地"""
    
    record = {
        "original_name": original_name,
        "archive_name": archive_name,
        "md5": md5,
        "password": password,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    # === 1. 尝试上传到云端 ===
    print("☁️ 正在呼叫 GitHub...") # 增加一条日志方便调试
    try:
        cloud_sync.update_cloud_keys(record)
    except Exception as e:
        print(f"❌ 云端同步出错了: {e}")

    # === 2. 本地也留一份（双重保险）===
    # 读取旧数据
    data = []
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = []

    data.append(record)

    # 写入本地
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)
    
    print(f"💾 [本地备份] 密钥已保存到 {DB_FILE}")
    
if __name__ == "__main__":
    # 这里我们先手动输入路径测试，后面再做拖拽
    target = input("👉 请输入你要打包的文件夹路径 (直接拖入文件夹到这里): ").strip('"') # .strip('"') 是为了去除可能的引号
    archive_folder(target)