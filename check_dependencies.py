"""
依赖检查工具
============
检查项目所需的 Python 包是否已安装。
可在应用启动时调用，或在需要时手动检查。
"""

from __future__ import annotations

from typing import Dict, List, Tuple


def check_dependencies() -> Tuple[bool, List[str], Dict[str, str]]:
    """
    检查所有依赖是否已安装。
    
    Returns:
        (all_ok, missing_packages, error_details)
        - all_ok: 是否所有依赖都已安装
        - missing_packages: 缺失的包列表
        - error_details: 每个包的详细错误信息
    """
    required_packages = {
        "streamlit": "streamlit",
        "pandas": "pandas",
        "openpyxl": "openpyxl",
        "openai": "openai",
        "python-docx": "docx",
        "pymupdf": "fitz",  # pymupdf 包导入时使用 fitz
        "easyocr": "easyocr",
        "yaml": "yaml",  # PyYAML
        "skimage": "skimage",  # scikit-image
        "tqdm": "tqdm",
    }
    
    missing = []
    errors = {}
    
    for package_name, import_name in required_packages.items():
        try:
            __import__(import_name)
        except ImportError as e:
            missing.append(package_name)
            errors[package_name] = str(e)
        except Exception as e:
            # 其他异常也记录，但可能不是缺失依赖
            errors[package_name] = f"导入异常: {str(e)}"
    
    all_ok = len(missing) == 0
    return all_ok, missing, errors


def get_install_command(missing_packages: List[str]) -> str:
    """生成安装命令"""
    if not missing_packages:
        return ""
    
    # 特殊处理 pymupdf（包名和导入名不同）
    package_list = []
    for pkg in missing_packages:
        if pkg == "pymupdf":
            package_list.append("pymupdf")
        elif pkg == "yaml":
            package_list.append("PyYAML")
        elif pkg == "skimage":
            package_list.append("scikit-image")
        else:
            package_list.append(pkg)
    
    return f"pip install {' '.join(package_list)}"


if __name__ == "__main__":
    """命令行直接运行时检查依赖"""
    all_ok, missing, errors = check_dependencies()
    
    if all_ok:
        print("✅ 所有依赖已安装")
    else:
        print("❌ 以下依赖缺失：")
        for pkg in missing:
            print(f"  - {pkg}")
            if pkg in errors:
                print(f"    错误：{errors[pkg]}")
        
        print("\n💡 安装命令：")
        print(f"  {get_install_command(missing)}")
        print("\n或安装所有依赖：")
        print("  pip install -r requirements.txt")
