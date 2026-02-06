import os
import subprocess
import hashlib
import json
import cloud_sync
import config_manager # <--- 引入新管家

# ================= 配置区域 =================
# 动态获取 7z 路径
SEVEN_ZIP_PATH = config_manager.get_7z_path()

DB_FILE = "local_keys_db.json"
RESTORE_DIR = "restored_files"
# ===========================================

# ... (后面的代码不用动)

def calculate_file_hash(filepath):
    """计算文件的 MD5 (和打包时一模一样的算法)"""
    print("⏳ 正在计算文件指纹，请稍候...")
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def find_password(file_md5):
    """直接从 GitHub 获取最新的密码本并查找"""
    
    # 调用云端模块下载数据
    data = cloud_sync.load_cloud_keys()
    
    if not data:
        return None

    # 遍历查找
    for record in data:
        # === 新增：安全检查 ===
        # 如果这条记录是坏的（没有 md5 字段），就跳过它，看下一条
        if 'md5' not in record:
            continue
        # ====================

        if record['md5'] == file_md5:
            return record
    return None

def unpack_archive(archive_path):
    # 1. 校验文件是否存在
    if not os.path.exists(archive_path):
        print("❌ 文件不存在！")
        return

    # 2. 计算指纹
    current_md5 = calculate_file_hash(archive_path)
    print(f"🏷️ 识别到指纹: {current_md5}")

    # 3. 查找密码
    record = find_password(current_md5)
    
    if not record:
        print("⚠️ 悲剧了：数据库里找不到这个文件的记录！")
        print("可能原因：1. 你没在本地备份过它  2. 文件被修改坏了")
        return

    password = record['password']
    original_name = record['original_name']
    print(f"✅ 找到记录！原始文件名: [{original_name}]")
    print(f"🔑 自动提取密码: {password}")

    # 4. 调用 7zip 解压
    # -o 后面紧跟输出路径（中间不能有空格，或者用引号包裹）
    # -y 表示如果有同名文件自动覆盖（你可以改成不加 -y 提示询问）
    output_path = os.path.join(RESTORE_DIR, original_name)
    
    cmd = [
        SEVEN_ZIP_PATH, 
        'x',               # x 表示完整解压（保留文件夹结构）
        archive_path, 
        f'-p{password}',   # 自动填入密码
        f'-o{RESTORE_DIR}', # 输出目录
        '-y'               # 自动确认覆盖
    ]

    print(f"📦 正在解压到: {output_path} ...")
    
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode == 0:
        print(f"✨ 成功还原！快去 {RESTORE_DIR} 看看吧！")
    else:
        print("❌ 解压失败，7zip 报错信息：")
        print(result.stderr)

if __name__ == "__main__":
    target = input("👉 请将要解压的 .7z 文件拖入这里: ").strip('"')
    unpack_archive(target)