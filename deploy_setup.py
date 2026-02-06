"""
部署设置工具
============
帮助管理员和用户快速配置部署环境。

使用方法：
  管理员模式：python deploy_setup.py --admin
  用户模式：  python deploy_setup.py --user --config <配置文件路径>
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from config_paths import (
    create_deployment_config,
    get_shared_data_file,
    get_local_config_dir,
    get_self_config_file,
)


def setup_shared_deployment():
    """设置共享部署（管理员使用）"""
    print("=" * 60)
    print("Digital Twin - 共享部署设置（管理员模式）")
    print("=" * 60)
    print()
    
    # 1. 选择共享数据位置
    print("步骤 1: 选择共享数据存储位置")
    print("提示：可以是网络驱动器路径，如：\\\\server\\shared\\digital_twin")
    print("      或本地共享文件夹路径，如：C:\\SharedData\\DigitalTwin")
    print()
    
    shared_path = input("请输入共享数据目录路径: ").strip()
    if not shared_path:
        print("❌ 路径不能为空")
        return False
    
    # 展开用户路径（如 ~）
    shared_path = os.path.expanduser(shared_path)
    
    # 验证路径
    if not os.path.exists(shared_path):
        create = input(f"路径不存在，是否创建？(y/n): ").strip().lower()
        if create == 'y':
            try:
                os.makedirs(shared_path, exist_ok=True)
                print(f"✅ 已创建目录：{shared_path}")
            except Exception as e:
                print(f"❌ 创建目录失败：{e}")
                return False
        else:
            print("❌ 请先创建共享目录")
            return False
    
    # 2. 创建配置文件
    config_file = os.path.join(shared_path, "deployment_config.json")
    if create_deployment_config(shared_path, save_path=config_file):
        print(f"✅ 配置文件已创建：{config_file}")
    else:
        print(f"❌ 配置文件创建失败")
        return False
    
    # 3. 初始化共享数据文件（如果不存在）
    try:
        from store_org import _create_empty_org_store, save_org_store
        
        shared_data_file = os.path.join(shared_path, "user_profiles_multi.json")
        if not os.path.exists(shared_data_file):
            # 临时设置环境变量，让 store_org 使用共享路径
            original_env = os.environ.get("DIGITAL_TWIN_SHARED_DIR")
            os.environ["DIGITAL_TWIN_SHARED_DIR"] = shared_path
            
            try:
                store = _create_empty_org_store()
                save_org_store(store)
                print(f"✅ 共享数据文件已初始化：{shared_data_file}")
            finally:
                # 恢复环境变量
                if original_env:
                    os.environ["DIGITAL_TWIN_SHARED_DIR"] = original_env
                elif "DIGITAL_TWIN_SHARED_DIR" in os.environ:
                    del os.environ["DIGITAL_TWIN_SHARED_DIR"]
        else:
            print(f"ℹ️  共享数据文件已存在：{shared_data_file}")
    except Exception as e:
        print(f"⚠️  初始化共享数据文件失败：{e}")
        print("   可以稍后手动创建或导入数据")
    
    print()
    print("=" * 60)
    print("✅ 共享部署设置完成！")
    print("=" * 60)
    print()
    print("下一步：")
    print("1. 将配置文件路径告知所有用户")
    print(f"   配置文件位置：{config_file}")
    print()
    print("2. 用户运行以下命令进行本地设置：")
    print(f"   python deploy_setup.py --user --config {config_file}")
    print()
    print("3. 或用户手动设置环境变量：")
    print(f"   Windows: set DIGITAL_TWIN_SHARED_DIR={shared_path}")
    print(f"   Linux/Mac: export DIGITAL_TWIN_SHARED_DIR={shared_path}")
    print()
    print("4. 或使用启动脚本（start_app.bat / start_app.sh）")
    
    return True


def setup_user_deployment(config_file: str = None):
    """设置用户本地部署"""
    print("=" * 60)
    print("Digital Twin - 用户本地设置")
    print("=" * 60)
    print()
    
    # 1. 读取共享配置
    if config_file:
        import json
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            shared_path = config.get("shared_data_path")
            if shared_path:
                print(f"✅ 已读取共享配置：{shared_path}")
            else:
                print("⚠️  配置文件中未找到 shared_data_path")
                shared_path = input("请输入共享数据目录路径: ").strip()
        except Exception as e:
            print(f"❌ 读取配置文件失败：{e}")
            shared_path = input("请输入共享数据目录路径: ").strip()
    else:
        shared_path = input("请输入共享数据目录路径: ").strip()
    
    if not shared_path:
        print("❌ 路径不能为空")
        return False
    
    shared_path = os.path.expanduser(shared_path)
    
    # 2. 验证共享路径可访问
    shared_data_file = os.path.join(shared_path, "user_profiles_multi.json")
    if not os.path.exists(shared_path):
        print(f"⚠️  警告：共享目录不存在：{shared_path}")
        print("   请确认路径正确，或联系管理员")
        confirm = input("是否继续？(y/n): ").strip().lower()
        if confirm != 'y':
            return False
    elif not os.path.exists(shared_data_file):
        print(f"⚠️  警告：共享数据文件不存在：{shared_data_file}")
        print("   请联系管理员初始化共享数据")
        confirm = input("是否继续？(y/n): ").strip().lower()
        if confirm != 'y':
            return False
    else:
        print(f"✅ 共享数据文件存在：{shared_data_file}")
    
    # 3. 设置本地配置目录
    local_path = get_local_config_dir()
    print(f"✅ 本地配置目录：{local_path}")
    
    # 4. 创建用户配置文件
    user_config_file = os.path.join(local_path, "deployment_config.json")
    if create_deployment_config(shared_path, local_path, user_config_file):
        print(f"✅ 用户配置文件已创建：{user_config_file}")
    else:
        print(f"❌ 用户配置文件创建失败")
        return False
    
    print()
    print("=" * 60)
    print("✅ 用户本地设置完成！")
    print("=" * 60)
    print()
    print("现在可以启动应用：")
    print("  streamlit run app.py")
    print()
    print("或使用启动脚本：")
    print("  start_app.bat  (Windows)")
    print("  ./start_app.sh (Linux/Mac)")
    print()
    print("首次使用请：")
    print("1. 在应用中切换到「个人版」")
    print("2. 绑定个人身份（输入姓名搜索并绑定）")
    print("3. 或直接使用「多人版」功能查看团队数据")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Digital Twin 部署设置工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  管理员模式：
    python deploy_setup.py --admin
  
  用户模式（使用配置文件）：
    python deploy_setup.py --user --config \\\\server\\shared\\digital_twin\\deployment_config.json
  
  用户模式（手动输入）：
    python deploy_setup.py --user
        """
    )
    parser.add_argument(
        "--admin",
        action="store_true",
        help="管理员模式：设置共享部署"
    )
    parser.add_argument(
        "--user",
        action="store_true",
        help="用户模式：设置本地配置"
    )
    parser.add_argument(
        "--config",
        type=str,
        help="配置文件路径（用户模式，可选）"
    )
    
    args = parser.parse_args()
    
    if args.admin:
        success = setup_shared_deployment()
        sys.exit(0 if success else 1)
    elif args.user:
        success = setup_user_deployment(args.config)
        sys.exit(0 if success else 1)
    else:
        parser.print_help()
        print()
        print("请指定模式：--admin（管理员）或 --user（用户）")
        sys.exit(1)
