"""
部署验证工具
============
快速检查部署配置是否正确，并显示访问信息。
"""

from __future__ import annotations

import os
import socket
from config_paths import (
    get_shared_data_file,
    get_self_config_file,
    get_local_config_dir,
    get_shared_data_dir,
)


def get_local_ip():
    """获取本机 IP 地址"""
    try:
        # 连接到一个远程地址来获取本机 IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def verify_deployment():
    """验证部署配置"""
    print("=" * 70)
    print("Digital Twin 部署验证")
    print("=" * 70)
    print()
    
    # 1. 检查共享数据配置
    print("[共享数据配置]")
    print("-" * 70)
    shared_dir = get_shared_data_dir()
    shared_file = get_shared_data_file()
    
    print(f"共享数据目录：{shared_dir}")
    print(f"共享数据文件：{shared_file}")
    
    if os.path.exists(shared_dir):
        print("[OK] 共享目录存在")
    else:
        print("[WARN] 共享目录不存在（首次部署需要创建）")
    
    if os.path.exists(shared_file):
        file_size = os.path.getsize(shared_file)
        print(f"[OK] 共享数据文件存在（大小：{file_size} 字节）")
    else:
        print("[WARN] 共享数据文件不存在（首次部署需要初始化）")
    
    print()
    
    # 2. 检查本地配置
    print("[本地配置]")
    print("-" * 70)
    local_dir = get_local_config_dir()
    self_config = get_self_config_file()
    
    print(f"本地配置目录：{local_dir}")
    print(f"个人配置文件：{self_config}")
    
    if os.path.exists(local_dir):
        print("[OK] 本地配置目录存在")
    else:
        print("[WARN] 本地配置目录不存在（将自动创建）")
    
    if os.path.exists(self_config):
        print("[OK] 个人配置文件存在")
        try:
            import json
            with open(self_config, "r", encoding="utf-8") as f:
                config = json.load(f)
            person_id = config.get("self_person_id")
            if person_id:
                print(f"   已绑定身份：person_id = {person_id}")
            else:
                print("   [WARN] 尚未绑定个人身份")
        except Exception:
            print("   [WARN] 配置文件格式异常")
    else:
        print("[INFO] 个人配置文件不存在（首次使用时会创建）")
    
    print()
    
    # 3. 检查环境变量
    print("[环境变量配置]")
    print("-" * 70)
    shared_env = os.getenv("DIGITAL_TWIN_SHARED_DIR")
    local_env = os.getenv("DIGITAL_TWIN_LOCAL_DIR")
    
    if shared_env:
        print(f"[OK] DIGITAL_TWIN_SHARED_DIR = {shared_env}")
    else:
        print("[INFO] DIGITAL_TWIN_SHARED_DIR 未设置（使用配置文件或默认路径）")
    
    if local_env:
        print(f"[OK] DIGITAL_TWIN_LOCAL_DIR = {local_env}")
    else:
        print("[INFO] DIGITAL_TWIN_LOCAL_DIR 未设置（使用配置文件或默认路径）")
    
    print()
    
    # 4. 检查依赖
    print("[依赖检查]")
    print("-" * 70)
    try:
        import streamlit
        print(f"[OK] Streamlit {streamlit.__version__}")
    except ImportError:
        print("[ERROR] Streamlit 未安装")
    
    try:
        import fitz
        print(f"[OK] PyMuPDF（PDF 导入功能可用）")
    except ImportError:
        print("[WARN] PyMuPDF 未安装（PDF 导入功能不可用）")
    
    try:
        import pandas
        print(f"[OK] Pandas {pandas.__version__}")
    except ImportError:
        print("[ERROR] Pandas 未安装")
    
    print()
    
    # 5. 访问信息
    print("[访问信息]")
    print("-" * 70)
    local_ip = get_local_ip()
    
    print("启动应用后，可通过以下地址访问：")
    print()
    print(f"  本地访问：http://localhost:8501")
    print(f"  网络访问：http://{local_ip}:8501")
    print()
    print("提示：")
    print("  - 本地访问：仅本机可以访问")
    print("  - 网络访问：同一局域网内的其他设备可以访问")
    print("  - 如果无法访问，请检查防火墙设置")
    
    print()
    
    # 6. 总结
    print("=" * 70)
    print("验证总结")
    print("=" * 70)
    
    issues = []
    if not os.path.exists(shared_dir):
        issues.append("共享目录不存在")
    if not os.path.exists(shared_file):
        issues.append("共享数据文件不存在（首次部署正常）")
    
    try:
        import streamlit
    except ImportError:
        issues.append("Streamlit 未安装")
    
    if issues:
        print("[WARN] 发现以下问题：")
        for issue in issues:
            print(f"   - {issue}")
        print()
        print("建议：")
        if "共享目录不存在" in issues:
            print("   运行：python deploy_setup.py --admin")
        if "Streamlit 未安装" in issues:
            print("   运行：pip install streamlit")
    else:
        print("[OK] 配置检查通过！")
        print()
        print("下一步：")
        print("  1. 运行：streamlit run app.py")
        print("  2. 在浏览器中打开显示的 Local URL")
        print("  3. 配置 API Key 并开始使用")
    
    print()
    print("=" * 70)


if __name__ == "__main__":
    verify_deployment()
