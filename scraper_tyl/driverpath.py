import os
import shutil
import platform
import subprocess

def find_chromedriver():
    # 1) 尝试 PATH
    path = shutil.which("chromedriver")
    if path:
        return path

    # 2) 按平台用命令行查找
    system = platform.system()
    try:
        if system == "Windows":
            result = subprocess.check_output("where chromedriver", shell=True, stderr=subprocess.DEVNULL)
        else:  # macOS / Linux
            result = subprocess.check_output("which chromedriver", shell=True, stderr=subprocess.DEVNULL)
        return result.decode().strip()
    except Exception:
        pass

    # 3) 手动常见路径搜索
    common_dirs = [
        os.path.expanduser("~/Downloads"),
        os.path.expanduser("~/"),
        "/usr/local/bin",
        "/usr/bin",
        "C:\\",
    ]
    for base in common_dirs:
        for root, dirs, files in os.walk(base):
            if "chromedriver" in files or "chromedriver.exe" in files:
                return os.path.join(root, "chromedriver" if system != "Windows" else "chromedriver.exe")
    return None


if __name__ == "__main__":
    path = find_chromedriver()
    if path:
        print("找到 chromedriver 路径:", path)
    else:
        print("未找到 chromedriver，请确认是否已安装。")
