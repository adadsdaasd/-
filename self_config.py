"""
Self Config (我是谁)
====================
管理"个人版"用户在 OrgStore 中的身份绑定。

设计：
- `self_config.json` 存储 `self_person_id`（绑定到 OrgStore 的某个 person）
- 个人版保存时会自动 upsert 到 OrgStore，并更新绑定
- 个人版读取时从 OrgStore 读取该 person 的完整信息（含所有 memberships）
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from store_org import (
    upsert_person,
    get_person_by_id,
    find_person_by_dedup_key,
    load_people,
    _extract_contact_from_profile,
    _compute_dedup_key,
    _normalize_phone,
)
from store_single import load_profile_single, save_profile_single


# 支持配置路径（部署模式）
try:
    from config_paths import get_self_config_file
    _USE_CONFIG_PATHS = True
except ImportError:
    _USE_CONFIG_PATHS = False

SELF_CONFIG_FILE = "self_config.json"


def _get_self_config_file() -> str:
    """获取个人配置文件路径（支持配置）"""
    if _USE_CONFIG_PATHS:
        return get_self_config_file()
    return SELF_CONFIG_FILE


def _load_self_config() -> Dict[str, Any]:
    """加载 self_config.json"""
    config_file = _get_self_config_file()
    if not os.path.exists(config_file):
        return {}
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_self_config(config: Dict[str, Any]) -> bool:
    """保存 self_config.json"""
    try:
        config_file = _get_self_config_file()
        # 确保目录存在
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


def get_self_person_id() -> Optional[str]:
    """获取当前绑定的 self_person_id"""
    config = _load_self_config()
    return config.get("self_person_id")


def set_self_person_id(person_id: str) -> bool:
    """设置当前绑定的 self_person_id"""
    config = _load_self_config()
    config["self_person_id"] = person_id
    return _save_self_config(config)


def clear_self_person_id() -> bool:
    """清除 self_person_id 绑定"""
    config = _load_self_config()
    config.pop("self_person_id", None)
    return _save_self_config(config)


def get_self_person() -> Optional[Dict[str, Any]]:
    """获取"我自己"的完整 person 信息（从 OrgStore 读取）"""
    person_id = get_self_person_id()
    if not person_id:
        return None
    return get_person_by_id(person_id)


def bind_self_by_phone(phone: str) -> Optional[str]:
    """
    按电话号码绑定"我自己"：
    - 如果 OrgStore 中已存在该电话的 person，绑定到它
    - 返回 person_id 或 None
    """
    if not phone:
        return None
    
    norm_phone = _normalize_phone(phone)
    if not norm_phone:
        return None
    
    dedup_key = f"phone:{norm_phone}"
    person = find_person_by_dedup_key(dedup_key)
    
    if person:
        person_id = person.get("id")
        set_self_person_id(person_id)
        return person_id
    
    return None


def save_self_profile(profile_data: Dict[str, Any], source: str) -> tuple:
    """
    保存"我自己"的档案：
    1. 写入 OrgStore（upsert，按电话去重）
    2. 绑定 self_person_id
    3. 同步写入 user_profile.json（兼容镜像）
    
    返回: (person_id, is_new, error_msg)
    """
    # 提取电话
    phone, email = _extract_contact_from_profile(profile_data)
    
    if not phone or phone == "未提及":
        return None, False, "电话是必填项，请补充电话信息"
    
    # upsert 到 OrgStore（不绑定任何小组，或绑定到"个人"小组）
    person_id, is_new = upsert_person(
        profile_data=profile_data,
        source=source,
        group_id=None,  # 个人版暂不分配小组
        membership_fields=None,
    )
    
    if not person_id:
        return None, False, "保存到 OrgStore 失败"
    
    # 绑定为"我自己"
    set_self_person_id(person_id)
    
    # 同步写入 user_profile.json（兼容镜像）
    save_profile_single(profile_data, source)
    
    return person_id, is_new, None


def load_self_profile_from_orgstore() -> Optional[Dict[str, Any]]:
    """
    从 OrgStore 加载"我自己"的档案（优先于 user_profile.json）
    
    返回格式与 load_profile_single() 兼容：
    {
        "source": "...",
        "created_at": "...",
        "profile": {...},
        "person_id": "...",  # 额外字段：OrgStore person ID
        "memberships": [...]  # 额外字段：所属小组信息
    }
    """
    person = get_self_person()
    if not person:
        return None
    
    profile = person.get("profile", {})
    sources = person.get("sources", [])
    
    # 取最新的 source
    source_type = "unknown"
    if sources:
        source_type = sources[-1].get("type", "unknown")
    
    return {
        "source": source_type,
        "created_at": person.get("created_at", ""),
        "updated_at": person.get("updated_at", ""),
        "profile": profile,
        "person_id": person.get("id"),
        "name": person.get("name"),
        "phone": person.get("phone"),
        "email": person.get("email"),
        "memberships": person.get("memberships", []),
    }


def migrate_single_to_orgstore() -> tuple:
    """
    迁移：将 user_profile.json 中的数据迁移到 OrgStore 并绑定为"我自己"
    
    返回: (success, message)
    """
    # 如果已经绑定了，不重复迁移
    if get_self_person_id():
        return True, "已有绑定，无需迁移"
    
    # 加载 user_profile.json
    single_data = load_profile_single()
    if not single_data:
        return True, "无个人版数据，无需迁移"
    
    profile = single_data.get("profile", {})
    source = single_data.get("source", "migration")
    
    # 如果 profile 是列表（文件上传的表格），取第一条
    if isinstance(profile, list):
        if len(profile) == 1:
            profile = profile[0]
        else:
            return False, "个人版数据为多行表格，请切换到多人版导入"
    
    if not isinstance(profile, dict):
        return False, "个人版数据格式异常"
    
    # 提取电话
    phone, email = _extract_contact_from_profile(profile)
    
    if not phone or phone == "未提及":
        return False, "个人版数据缺少电话，无法迁移（电话是必填项）"
    
    # 检查 OrgStore 中是否已有该电话
    dedup_key = f"phone:{_normalize_phone(phone)}"
    existing = find_person_by_dedup_key(dedup_key)
    
    if existing:
        # 已存在，直接绑定
        set_self_person_id(existing.get("id"))
        return True, f"已绑定到 OrgStore 中的「{existing.get('name')}」"
    
    # 不存在，创建新 person
    person_id, is_new, error = save_self_profile(profile, source)
    
    if error:
        return False, error
    
    return True, f"已迁移到 OrgStore 并绑定（person_id: {person_id}）"


def search_self_by_name(name: str) -> list:
    """
    按姓名搜索可能的"我自己"候选人（用于手动选择绑定）
    
    返回: [{person_id, name, phone, email}, ...]
    """
    if not name:
        return []
    
    name_lower = name.lower().strip()
    people = load_people()
    
    candidates = []
    for p in people:
        p_name = p.get("name", "").lower()
        if name_lower in p_name or p_name in name_lower:
            candidates.append({
                "person_id": p.get("id"),
                "name": p.get("name"),
                "phone": p.get("phone"),
                "email": p.get("email"),
            })
    
    return candidates
