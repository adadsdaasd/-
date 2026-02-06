"""
数据路径配置管理
================
支持环境变量和配置文件两种方式配置数据存储路径。

设计目标：
- 多人版数据：共享位置（网络驱动器/共享文件夹）
- 个人版配置：本地用户目录（每个用户独立）
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

# 默认文件名
DEFAULT_SHARED_DATA_FILE = "user_profiles_multi.json"
DEFAULT_SELF_CONFIG_FILE = "self_config.json"
DEFAULT_USER_PROFILE_FILE = "user_profile.json"

# 环境变量名
ENV_SHARED_DATA_DIR = "DIGITAL_TWIN_SHARED_DIR"
ENV_LOCAL_CONFIG_DIR = "DIGITAL_TWIN_LOCAL_DIR"
ENV_CONFIG_FILE = "DIGITAL_TWIN_CONFIG"

# 配置文件路径
CONFIG_FILE_NAME = "deployment_config.json"

# 缓存配置（避免重复读取）
_cached_config: Optional[dict] = None


def get_shared_data_dir() -> str:
    """
    获取共享数据目录（多人版数据存储位置）
    
    优先级：
    1. 环境变量 DIGITAL_TWIN_SHARED_DIR
    2. 配置文件中的 shared_data_path
    3. 当前目录（默认）
    
    Returns:
        共享数据目录的绝对路径
    """
    # 1. 环境变量
    env_path = os.getenv(ENV_SHARED_DATA_DIR)
    if env_path:
        abs_path = os.path.abspath(os.path.expanduser(env_path))
        # 确保目录存在
        os.makedirs(abs_path, exist_ok=True)
        return abs_path
    
    # 2. 配置文件
    config = _load_deployment_config()
    if config and "shared_data_path" in config:
        abs_path = os.path.abspath(os.path.expanduser(config["shared_data_path"]))
        os.makedirs(abs_path, exist_ok=True)
        return abs_path
    
    # 3. 默认：当前目录
    return os.getcwd()


def get_local_config_dir() -> str:
    """
    获取本地配置目录（个人版配置存储位置）
    
    优先级：
    1. 环境变量 DIGITAL_TWIN_LOCAL_DIR
    2. 配置文件中的 local_config_path
    3. 用户目录下的 DigitalTwin 文件夹
    
    Returns:
        本地配置目录的绝对路径
    """
    # 1. 环境变量
    env_path = os.getenv(ENV_LOCAL_CONFIG_DIR)
    if env_path:
        abs_path = os.path.abspath(os.path.expanduser(env_path))
        os.makedirs(abs_path, exist_ok=True)
        return abs_path
    
    # 2. 配置文件
    config = _load_deployment_config()
    if config and "local_config_path" in config:
        abs_path = os.path.abspath(os.path.expanduser(config["local_config_path"]))
        os.makedirs(abs_path, exist_ok=True)
        return abs_path
    
    # 3. 默认：用户目录下的 DigitalTwin
    user_home = os.path.expanduser("~")
    default_path = os.path.join(user_home, "DigitalTwin")
    try:
        os.makedirs(default_path, exist_ok=True)
    except (PermissionError, OSError):
        # 如果无法创建，使用当前目录
        default_path = os.path.join(os.getcwd(), "local_config")
        os.makedirs(default_path, exist_ok=True)
    return default_path


def get_shared_data_file() -> str:
    """获取共享数据文件完整路径"""
    return os.path.join(get_shared_data_dir(), DEFAULT_SHARED_DATA_FILE)


def get_self_config_file() -> str:
    """获取个人配置文件完整路径"""
    return os.path.join(get_local_config_dir(), DEFAULT_SELF_CONFIG_FILE)


def get_user_profile_file() -> str:
    """获取个人版数据文件完整路径（兼容镜像）"""
    return os.path.join(get_local_config_dir(), DEFAULT_USER_PROFILE_FILE)


def _load_deployment_config() -> Optional[dict]:
    """
    加载部署配置文件
    
    优先级：
    1. 环境变量 DIGITAL_TWIN_CONFIG 指定的文件
    2. 当前目录下的 deployment_config.json
    3. 用户目录下的 deployment_config.json
    """
    global _cached_config
    
    # 使用缓存（避免重复读取）
    if _cached_config is not None:
        return _cached_config
    
    # 1. 环境变量指定的配置文件
    config_file_env = os.getenv(ENV_CONFIG_FILE)
    if config_file_env and os.path.exists(config_file_env):
        try:
            with open(config_file_env, "r", encoding="utf-8") as f:
                _cached_config = json.load(f)
                return _cached_config
        except Exception:
            pass
    
    # 2. 当前目录下的配置文件
    config_file = os.path.join(os.getcwd(), CONFIG_FILE_NAME)
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                _cached_config = json.load(f)
                return _cached_config
        except Exception:
            pass
    
    # 3. 用户目录下的配置文件（避免递归，直接计算默认路径）
    user_home = os.path.expanduser("~")
    default_local_path = os.path.join(user_home, "DigitalTwin")
    user_config_file = os.path.join(default_local_path, CONFIG_FILE_NAME)
    if os.path.exists(user_config_file):
        try:
            with open(user_config_file, "r", encoding="utf-8") as f:
                _cached_config = json.load(f)
                return _cached_config
        except Exception:
            pass
    
    _cached_config = {}
    return _cached_config


def create_deployment_config(
    shared_data_path: str,
    local_config_path: Optional[str] = None,
    save_path: Optional[str] = None
) -> bool:
    """
    创建部署配置文件
    
    Args:
        shared_data_path: 共享数据目录路径
        local_config_path: 本地配置目录路径（可选）
        save_path: 配置文件保存路径（默认当前目录）
    
    Returns:
        是否创建成功
    """
    config = {
        "shared_data_path": os.path.abspath(os.path.expanduser(shared_data_path)),
        "local_config_path": (
            os.path.abspath(os.path.expanduser(local_config_path))
            if local_config_path
            else os.path.join(os.path.expanduser("~"), "DigitalTwin")
        ),
        "version": "1.0",
        "description": "Digital Twin 部署配置 - 多人版数据共享，个人版配置独立"
    }
    
    save_file = save_path or os.path.join(os.getcwd(), CONFIG_FILE_NAME)
    try:
        # 确保目录存在
        os.makedirs(os.path.dirname(save_file), exist_ok=True)
        
        with open(save_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"创建配置文件失败：{e}")
        return False


def clear_config_cache():
    """清除配置缓存（用于测试或重新加载配置）"""
    global _cached_config
    _cached_config = None


if __name__ == "__main__":
    """测试配置路径功能"""
    print("=" * 60)
    print("配置路径测试")
    print("=" * 60)
    print()
    
    print(f"共享数据目录：{get_shared_data_dir()}")
    print(f"共享数据文件：{get_shared_data_file()}")
    print()
    
    print(f"本地配置目录：{get_local_config_dir()}")
    print(f"个人配置文件：{get_self_config_file()}")
    print(f"个人数据文件：{get_user_profile_file()}")
    print()
    
    config = _load_deployment_config()
    if config:
        print("部署配置：")
        print(json.dumps(config, indent=2, ensure_ascii=False))
    else:
        print("未找到部署配置文件（使用默认配置）")
