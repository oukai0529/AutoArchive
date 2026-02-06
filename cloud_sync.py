import requests
import json
import sys
import config_manager  # <--- 引入新管家

# ================= 你的 GitHub 配置 (已改为动态读取) =================
# 1. 从配置管家那里获取 Token
GITHUB_TOKEN = config_manager.get_token()

# 2. 从配置管家那里获取 Gist ID
GIST_ID = config_manager.get_gist_id()

# 3. Gist 里的文件名
FILENAME = "keys_db.json"
# ===================================================

# 下面的代码保持不变...
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}
# ... (后面的函数不用动)

def load_cloud_keys():
    """从 GitHub 下载最新的密码本"""
    print("☁️ 正在从 GitHub 同步数据...")
    url = f"https://api.github.com/gists/{GIST_ID}"
    
    try:
        response = requests.get(url, headers=HEADERS)
        if response.status_code == 200:
            content = response.json()['files'][FILENAME]['content']
            return json.loads(content)
        else:
            print(f"❌ 下载失败: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return []

def update_cloud_keys(new_record):
    """把新记录上传到 GitHub"""
    
    # 1. 先下载旧数据（防止把别人的覆盖了）
    current_data = load_cloud_keys()
    
    # 2. 追加新记录
    current_data.append(new_record)
    
    # 3. 准备上传
    print("☁️ 正在上传新记录到 GitHub...")
    url = f"https://api.github.com/gists/{GIST_ID}"
    
    payload = {
        "files": {
            FILENAME: {
                "content": json.dumps(current_data, indent=4, ensure_ascii=False)
            }
        }
    }
    
    try:
        response = requests.patch(url, headers=HEADERS, json=payload)
        if response.status_code == 200:
            print("✅ 云端同步成功！")
            return True
        else:
            print(f"❌ 上传失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 网络错误: {e}")
        return False

# 测试代码
if __name__ == "__main__":
    # 这是一个测试，运行这个脚本会往云端写一条假数据
    test_record = {"test": "connection_success", "time": "now"}
    update_cloud_keys(test_record)