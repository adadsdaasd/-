"""
个人版存储层 (Single Profile Store)
=================================
将个人版的 JSON 存取从 UI 中解耦出来，便于多模块复用。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Optional, Dict


# 支持配置路径（部署模式）
try:
    from config_paths import get_user_profile_file
    _USE_CONFIG_PATHS = True
except ImportError:
    _USE_CONFIG_PATHS = False

PROFILE_FILE_SINGLE = "user_profile.json"


def _get_profile_file_single() -> str:
    """获取个人版数据文件路径（支持配置）"""
    if _USE_CONFIG_PATHS:
        return get_user_profile_file()
    return PROFILE_FILE_SINGLE


def _get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def single_profile_exists() -> bool:
    return os.path.exists(_get_profile_file_single())


def load_profile_single() -> Optional[Dict]:
    """加载单人画像（个人版）"""
    if not single_profile_exists():
        return None

    try:
        with open(_get_profile_file_single(), "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def save_profile_single(profile_data: Any, source: str) -> bool:
    """保存单人画像（个人版）"""
    try:
        data = {
            "source": source,
            "created_at": _get_timestamp(),
            "profile": profile_data,
        }
        profile_file = _get_profile_file_single()
        os.makedirs(os.path.dirname(profile_file), exist_ok=True)
        with open(profile_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def delete_profile_single() -> bool:
    """删除个人版存储文件"""
    if not single_profile_exists():
        return True
    try:
        os.remove(_get_profile_file_single())
        return True
    except Exception:
        return False

