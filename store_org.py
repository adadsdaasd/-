"""
多人版存储层 (OrgStore v2)
=========================
负责多人版的组织/小组/人员/组内信息的读写、迁移与去重 upsert。

设计原则：
- 不依赖 Streamlit（不使用 st.session_state / st.xxx），纯数据层
- UI 负责选择 group_id，并将其传入存储层
"""

from __future__ import annotations

import json
import os
import re
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# 支持配置路径（部署模式）
try:
    from config_paths import get_shared_data_file
    _USE_CONFIG_PATHS = True
except ImportError:
    _USE_CONFIG_PATHS = False

PROFILE_FILE_MULTI = "user_profiles_multi.json"
SCHEMA_VERSION = 3


def _get_profile_file_multi() -> str:
    """获取多人版数据文件路径（支持配置）"""
    if _USE_CONFIG_PATHS:
        return get_shared_data_file()
    return PROFILE_FILE_MULTI


def _get_timestamp() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def org_store_exists() -> bool:
    return os.path.exists(_get_profile_file_multi())


def delete_org_store_file() -> bool:
    if not org_store_exists():
        return True
    try:
        os.remove(_get_profile_file_multi())
        return True
    except Exception:
        return False


def _normalize_phone(phone: str) -> str:
    """归一化电话号码：去除空格、横线等"""
    if not phone or phone == "未提及":
        return ""
    return re.sub(r"[\s\-\(\)]+", "", str(phone).strip())


def _normalize_email(email: str) -> str:
    """归一化邮箱：转小写、去除空格"""
    if not email or email == "未提及":
        return ""
    return str(email).strip().lower()


def _compute_dedup_key(phone: str, email: str) -> dict:
    """
    计算去重键（phone_then_email 策略）
    返回 {"strategy": "phone_then_email", "key": "phone:xxx" 或 "email:xxx" 或 ""}
    """
    norm_phone = _normalize_phone(phone)
    norm_email = _normalize_email(email)

    if norm_phone:
        return {"strategy": "phone_then_email", "key": f"phone:{norm_phone}"}
    elif norm_email:
        return {"strategy": "phone_then_email", "key": f"email:{norm_email}"}
    else:
        return {"strategy": "phone_then_email", "key": ""}


def _extract_contact_from_profile(profile_data: dict) -> Tuple[str, str]:
    """从 profile 中提取电话和邮箱"""
    if not isinstance(profile_data, dict):
        return "", ""

    phone = ""
    email = ""

    phone_keys = ["电话", "联系电话", "手机", "phone", "tel", "mobile"]
    for key in phone_keys:
        if key in profile_data and profile_data[key]:
            phone = str(profile_data[key])
            break

    contact = profile_data.get("联系方式", {})
    if isinstance(contact, dict):
        if not phone:
            phone = contact.get("电话", "")
        email = contact.get("邮箱", "")

    email_keys = ["邮箱", "联系邮箱", "email", "e-mail"]
    for key in email_keys:
        if key in profile_data and profile_data[key]:
            email = str(profile_data[key])
            break

    return phone, email


def _create_empty_org_store() -> dict:
    return {
        "_schema_version": SCHEMA_VERSION,
        "org": {
            "id": "org_default",
            "name": "大团队",
            "created_at": _get_timestamp(),
            "updated_at": _get_timestamp(),
        },
        "groups": [],
        "people": [],
    }


def _migrate_member_to_store(store: dict, old_member: dict, group_id: str):
    """将旧成员迁移到新 store（含去重）"""
    profile = old_member.get("profile", {})

    phone, email = _extract_contact_from_profile(profile)
    dedup = _compute_dedup_key(phone, email)

    name = "未知"
    if isinstance(profile, dict):
        name = profile.get("姓名", old_member.get("name", "未知"))
        if name == "未提及":
            name = old_member.get("name", f"成员_{old_member.get('id', '')[:4]}")

    existing_person = None
    if dedup["key"]:
        for p in store["people"]:
            if p.get("dedup", {}).get("key") == dedup["key"]:
                existing_person = p
                break

    membership = {
        "group_id": group_id,
        "joined_at": old_member.get("created_at", _get_timestamp()),
        "updated_at": _get_timestamp(),
        "fields": {"source": old_member.get("source", "unknown")},
    }

    if existing_person:
        existing_ms = [
            m
            for m in existing_person.get("memberships", [])
            if m.get("group_id") == group_id
        ]
        if not existing_ms:
            existing_person.setdefault("memberships", []).append(membership)
        existing_person["updated_at"] = _get_timestamp()
    else:
        new_person = {
            "id": old_member.get("id", str(uuid.uuid4())[:8]),
            "name": name,
            "phone": _normalize_phone(phone),
            "email": _normalize_email(email),
            "dedup": dedup,
            "created_at": old_member.get("created_at", _get_timestamp()),
            "updated_at": _get_timestamp(),
            "profile": profile,
            "sources": [
                {
                    "type": old_member.get("source", "unknown"),
                    "imported_at": old_member.get("created_at", _get_timestamp()),
                }
            ],
            "memberships": [membership],
        }
        store["people"].append(new_person)


def _migrate_from_v1(old_data: Any) -> dict:
    """从旧格式迁移到 v2 格式"""
    store = _create_empty_org_store()

    if isinstance(old_data, list) and len(old_data) > 0:
        first_item = old_data[0]

        # 旧团队格式：[{id,name,members:[...]}]
        if isinstance(first_item, dict) and "members" in first_item:
            for old_team in old_data:
                group_id = old_team.get("id", str(uuid.uuid4())[:8])
                group_name = old_team.get("name", "默认小组")

                store["groups"].append(
                    {
                        "id": group_id,
                        "name": group_name,
                        "description": "",
                        "tags": [],
                        "created_at": old_team.get("created_at", _get_timestamp()),
                        "updated_at": _get_timestamp(),
                    }
                )

                for old_member in old_team.get("members", []):
                    _migrate_member_to_store(store, old_member, group_id)

        # 更老的扁平成员列表：[{id,profile,...}]
        elif isinstance(first_item, dict) and "profile" in first_item:
            default_group_id = "default_group"
            store["groups"].append(
                {
                    "id": default_group_id,
                    "name": "默认小组",
                    "description": "从旧数据迁移",
                    "tags": [],
                    "created_at": _get_timestamp(),
                    "updated_at": _get_timestamp(),
                }
            )

            for old_member in old_data:
                _migrate_member_to_store(store, old_member, default_group_id)

    return store


def _migrate_v2_to_v3(store: dict) -> dict:
    """v2 → v3 迁移：为所有 person 补齐 performance 字段"""
    from performance_models import ensure_performance
    for person in store.get("people", []):
        ensure_performance(person)
    store["_schema_version"] = SCHEMA_VERSION
    return store


def load_org_store() -> dict:
    """加载 OrgStore（含自动迁移 v1→v2→v3）"""
    if not org_store_exists():
        return _create_empty_org_store()

    try:
        with open(_get_profile_file_multi(), "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict) and data.get("_schema_version") == SCHEMA_VERSION:
            return data

        # v2 → v3（已是 dict 但版本为 2）
        if isinstance(data, dict) and data.get("_schema_version") == 2:
            migrated = _migrate_v2_to_v3(data)
            save_org_store(migrated)
            return migrated

        # v1 → v2 → v3（旧 list 格式）
        migrated = _migrate_from_v1(data)
        migrated = _migrate_v2_to_v3(migrated)
        save_org_store(migrated)
        return migrated

    except Exception:
        return _create_empty_org_store()


def save_org_store(store: dict) -> bool:
    """保存 OrgStore"""
    try:
        store["_schema_version"] = SCHEMA_VERSION
        with open(_get_profile_file_multi(), "w", encoding="utf-8") as f:
            json.dump(store, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False


# ==================== 组织操作 ====================


def get_organization() -> dict:
    store = load_org_store()
    return store.get("org", {})


def update_organization(name: Optional[str] = None) -> bool:
    store = load_org_store()
    if name:
        store.setdefault("org", {})["name"] = name
    store.setdefault("org", {})["updated_at"] = _get_timestamp()
    return save_org_store(store)


# ==================== 小组操作 ====================


def load_groups() -> List[Dict]:
    store = load_org_store()
    return store.get("groups", [])


def create_group(group_name: str, description: str = "", tags: Optional[list] = None) -> str:
    store = load_org_store()
    group_id = str(uuid.uuid4())[:8]
    store.setdefault("groups", []).append(
        {
            "id": group_id,
            "name": group_name,
            "description": description,
            "tags": tags or [],
            "created_at": _get_timestamp(),
            "updated_at": _get_timestamp(),
        }
    )
    save_org_store(store)
    return group_id


def rename_group(group_id: str, new_name: str) -> bool:
    store = load_org_store()
    for group in store.get("groups", []):
        if group.get("id") == group_id:
            group["name"] = new_name
            group["updated_at"] = _get_timestamp()
            return save_org_store(store)
    return False


def delete_group(group_id: str) -> bool:
    store = load_org_store()
    store["groups"] = [g for g in store.get("groups", []) if g.get("id") != group_id]

    for person in store.get("people", []):
        person["memberships"] = [
            m for m in person.get("memberships", []) if m.get("group_id") != group_id
        ]

    return save_org_store(store)


def get_group_by_id(group_id: str) -> Optional[Dict]:
    store = load_org_store()
    for group in store.get("groups", []):
        if group.get("id") == group_id:
            return group
    return None


# ==================== 人员操作（含去重）====================


def load_people() -> List[Dict]:
    store = load_org_store()
    return store.get("people", [])


def find_person_by_dedup_key(dedup_key: str) -> Optional[Dict]:
    if not dedup_key:
        return None
    store = load_org_store()
    for person in store.get("people", []):
        if person.get("dedup", {}).get("key") == dedup_key:
            return person
    return None


def upsert_person(
    profile_data: dict,
    source: str,
    group_id: Optional[str] = None,
    membership_fields: Optional[dict] = None,
) -> Tuple[Optional[str], bool]:
    """
    新增或更新人员（含去重）
    返回: (person_id, is_new)
    """
    store = load_org_store()

    phone, email = _extract_contact_from_profile(profile_data)
    dedup = _compute_dedup_key(phone, email)

    name = "未知"
    if isinstance(profile_data, dict):
        name = profile_data.get("姓名", "未知")
        if name == "未提及":
            name = f"成员_{str(uuid.uuid4())[:4]}"

    existing_person = None
    if dedup["key"]:
        for p in store.get("people", []):
            if p.get("dedup", {}).get("key") == dedup["key"]:
                existing_person = p
                break

    membership = None
    if group_id:
        membership = {
            "group_id": group_id,
            "joined_at": _get_timestamp(),
            "updated_at": _get_timestamp(),
            "fields": membership_fields or {"source": source},
        }

    if existing_person:
        existing_person["updated_at"] = _get_timestamp()

        if isinstance(profile_data, dict) and isinstance(existing_person.get("profile"), dict):
            for key, value in profile_data.items():
                if value and value != "未提及":
                    existing_person["profile"][key] = value

        existing_person.setdefault("sources", []).append(
            {"type": source, "imported_at": _get_timestamp()}
        )

        if membership:
            existing_ms = None
            for ms in existing_person.get("memberships", []):
                if ms.get("group_id") == group_id:
                    existing_ms = ms
                    break
            if existing_ms:
                existing_ms["updated_at"] = _get_timestamp()
                existing_ms.setdefault("fields", {}).update(membership_fields or {})
            else:
                existing_person.setdefault("memberships", []).append(membership)

        save_org_store(store)
        return existing_person.get("id"), False

    from performance_models import empty_performance

    person_id = str(uuid.uuid4())[:8]
    new_person = {
        "id": person_id,
        "name": name,
        "phone": _normalize_phone(phone),
        "email": _normalize_email(email),
        "dedup": dedup,
        "created_at": _get_timestamp(),
        "updated_at": _get_timestamp(),
        "profile": profile_data,
        "sources": [{"type": source, "imported_at": _get_timestamp()}],
        "memberships": [membership] if membership else [],
        "performance": empty_performance(),
    }
    store.setdefault("people", []).append(new_person)
    save_org_store(store)
    return person_id, True


def get_person_by_id(person_id: str) -> Optional[Dict]:
    store = load_org_store()
    for person in store.get("people", []):
        if person.get("id") == person_id:
            return person
    return None


def delete_person(person_id: str) -> bool:
    store = load_org_store()
    store["people"] = [p for p in store.get("people", []) if p.get("id") != person_id]
    return save_org_store(store)


def get_people_in_group(group_id: str) -> List[Dict]:
    store = load_org_store()
    result = []
    for person in store.get("people", []):
        for ms in person.get("memberships", []):
            if ms.get("group_id") == group_id:
                result.append({"person": person, "membership": ms})
                break
    return result


def get_person_groups(person_id: str) -> List[Dict]:
    person = get_person_by_id(person_id)
    if not person:
        return []
    result = []
    for ms in person.get("memberships", []):
        group = get_group_by_id(ms.get("group_id"))
        if group:
            result.append({"group": group, "membership": ms})
    return result


def add_person_to_group(person_id: str, group_id: str, fields: Optional[dict] = None) -> bool:
    store = load_org_store()
    for person in store.get("people", []):
        if person.get("id") == person_id:
            for ms in person.get("memberships", []):
                if ms.get("group_id") == group_id:
                    ms["updated_at"] = _get_timestamp()
                    if fields:
                        ms.setdefault("fields", {}).update(fields)
                    return save_org_store(store)
            person.setdefault("memberships", []).append(
                {
                    "group_id": group_id,
                    "joined_at": _get_timestamp(),
                    "updated_at": _get_timestamp(),
                    "fields": fields or {},
                }
            )
            return save_org_store(store)
    return False


def remove_person_from_group(person_id: str, group_id: str) -> bool:
    store = load_org_store()
    for person in store.get("people", []):
        if person.get("id") == person_id:
            person["memberships"] = [
                m for m in person.get("memberships", []) if m.get("group_id") != group_id
            ]
            return save_org_store(store)
    return False


def update_membership_fields(person_id: str, group_id: str, fields: dict) -> bool:
    store = load_org_store()
    for person in store.get("people", []):
        if person.get("id") == person_id:
            for ms in person.get("memberships", []):
                if ms.get("group_id") == group_id:
                    ms["updated_at"] = _get_timestamp()
                    ms.setdefault("fields", {}).update(fields)
                    return save_org_store(store)
    return False


# ==================== 兼容性函数（供其他模块调用）====================
# 这些函数保持与旧代码的接口兼容，内部使用新的 OrgStore 结构


def load_teams() -> list:
    return load_groups()


def save_teams(teams: list) -> bool:
    store = load_org_store()
    store["groups"] = teams
    return save_org_store(store)


def create_team(team_name: str) -> str:
    return create_group(team_name)


def rename_team(team_id: str, new_name: str) -> bool:
    return rename_group(team_id, new_name)


def delete_team(team_id: str) -> bool:
    return delete_group(team_id)


def get_team_by_id(team_id: str) -> Optional[Dict]:
    return get_group_by_id(team_id)


def add_member_to_team(team_id: str, profile_data: dict, source: str) -> bool:
    person_id, _ = upsert_person(profile_data, source, group_id=team_id)
    return person_id is not None


def delete_member_from_team(team_id: str, member_id: str) -> bool:
    return remove_person_from_group(member_id, team_id)


def get_member_by_id(team_id: str, member_id: str) -> Optional[Dict]:
    person = get_person_by_id(member_id)
    if not person:
        return None
    for ms in person.get("memberships", []):
        if ms.get("group_id") == team_id:
            return {
                "id": person.get("id"),
                "name": person.get("name"),
                "source": ms.get("fields", {}).get("source", "unknown"),
                "created_at": person.get("created_at"),
                "profile": person.get("profile"),
                "membership": ms,
            }
    return None


def load_profiles_multi() -> list:
    people = load_people()
    result = []
    for person in people:
        group_names = []
        for ms in person.get("memberships", []):
            group = get_group_by_id(ms.get("group_id"))
            if group:
                group_names.append(group.get("name"))
        result.append(
            {
                "id": person.get("id"),
                "name": person.get("name"),
                "profile": person.get("profile", {}),
                "source": (person.get("sources", [{}]) or [{}])[0].get("type", "unknown"),
                "created_at": person.get("created_at", ""),
                "groups": group_names,
                "memberships": person.get("memberships", []),
            }
        )
    return result


def add_profile_multi(profile_data: Any, source: str, group_id: Optional[str] = None) -> bool:
    """
    兼容旧代码：添加成员到指定小组（若 group_id 为空则使用默认/第一个小组）
    """
    # group_id 为空：确保至少存在一个默认小组
    if not group_id:
        groups = load_groups()
        if not groups:
            group_id = create_group("默认小组")
        else:
            group_id = groups[0].get("id")
    person_id, _ = upsert_person(profile_data, source, group_id=group_id)
    return person_id is not None


def delete_profile_multi(profile_id: str) -> bool:
    return delete_person(profile_id)


def get_profile_by_id(profile_id: str) -> Optional[Dict]:
    person = get_person_by_id(profile_id)
    if not person:
        return None

    group_names = []
    for ms in person.get("memberships", []):
        group = get_group_by_id(ms.get("group_id"))
        if group:
            group_names.append(group.get("name"))

    return {
        "id": person.get("id"),
        "name": person.get("name"),
        "profile": person.get("profile", {}),
        "source": (person.get("sources", [{}]) or [{}])[0].get("type", "unknown"),
        "created_at": person.get("created_at", ""),
        "groups": group_names,
        "memberships": person.get("memberships", []),
        "performance": person.get("performance", {}),
    }


# ==================== 绩效操作 ====================


def get_person_performance(person_id: str) -> Dict:
    """获取某人的 performance 字段"""
    from performance_models import ensure_performance, empty_performance
    person = get_person_by_id(person_id)
    if not person:
        return empty_performance()
    ensure_performance(person)
    return person["performance"]


def set_person_base_score(person_id: str, base_score: float, note: str = "") -> bool:
    """设置某人的基准分"""
    from performance_models import ensure_performance, _now
    store = load_org_store()
    for person in store.get("people", []):
        if person.get("id") == person_id:
            ensure_performance(person)
            person["performance"]["base_score"] = float(base_score)
            person["performance"]["updated_at"] = _now()
            return save_org_store(store)
    return False


def add_performance_event(person_id: str, event: Dict) -> bool:
    """向某人添加一条绩效事件"""
    from performance_models import ensure_performance, _now
    store = load_org_store()
    for person in store.get("people", []):
        if person.get("id") == person_id:
            ensure_performance(person)
            person["performance"]["events"].append(event)
            person["performance"]["updated_at"] = _now()
            return save_org_store(store)
    return False


def update_performance_event(person_id: str, event_id: str, patch: Dict) -> bool:
    """更新某人的一条绩效事件（局部更新）"""
    from performance_models import ensure_performance, _now
    store = load_org_store()
    for person in store.get("people", []):
        if person.get("id") == person_id:
            ensure_performance(person)
            for event in person["performance"]["events"]:
                if event.get("id") == event_id:
                    event.update(patch)
                    person["performance"]["updated_at"] = _now()
                    return save_org_store(store)
    return False


def delete_performance_event(person_id: str, event_id: str) -> bool:
    """删除某人的一条绩效事件"""
    from performance_models import ensure_performance, _now
    store = load_org_store()
    for person in store.get("people", []):
        if person.get("id") == person_id:
            ensure_performance(person)
            before_len = len(person["performance"]["events"])
            person["performance"]["events"] = [
                e for e in person["performance"]["events"] if e.get("id") != event_id
            ]
            if len(person["performance"]["events"]) < before_len:
                person["performance"]["updated_at"] = _now()
                return save_org_store(store)
    return False

