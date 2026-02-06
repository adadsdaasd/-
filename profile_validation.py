"""
Profile completeness validation
================================
用于统一校验“个人信息是否完整”，并返回缺失项列表。

设计目标：
- 兼容多来源数据（AI 文本分析 dict、表格导入的行 dict、研究档案 dict）
- 对常见“未提及/空字符串/空列表”等缺失值做统一处理
- 支持不同校验 Schema（general / research）
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


MISSING_STRINGS = {
    "",
    "未提及",
    "未知",
    "无",
    "none",
    "null",
    "n/a",
    "na",
}


def _is_missing_str(value: str) -> bool:
    s = value.strip()
    return s == "" or s.lower() in MISSING_STRINGS


def is_missing(value: Any) -> bool:
    """判断是否为缺失值"""
    if value is None:
        return True

    if isinstance(value, str):
        return _is_missing_str(value)

    if isinstance(value, (int, float)):
        # 数值型：0 不视为缺失
        return False

    if isinstance(value, list):
        # 列表：只要有一个非缺失元素就算不缺失
        for item in value:
            if not is_missing(item):
                return False
        return True

    if isinstance(value, dict):
        # 字典：空字典视为缺失
        return len(value) == 0

    return False


def _get_first_non_missing(mapping: Dict[str, Any], keys: List[str]) -> str:
    for k in keys:
        if k in mapping and not is_missing(mapping.get(k)):
            return str(mapping.get(k)).strip()
    return ""


def extract_contact(profile: Dict[str, Any]) -> Tuple[str, str]:
    """从 profile 中提取 phone/email（兼容多种字段名与嵌套结构）"""
    if not isinstance(profile, dict):
        return "", ""

    phone_keys = ["电话", "联系电话", "手机", "phone", "tel", "mobile"]
    email_keys = ["邮箱", "联系邮箱", "email", "e-mail"]

    phone = _get_first_non_missing(profile, phone_keys)
    email = _get_first_non_missing(profile, email_keys)

    contact = profile.get("联系方式", {})
    if isinstance(contact, dict):
        if not phone:
            phone = _get_first_non_missing(contact, ["电话", "phone", "tel", "mobile"])
        if not email:
            email = _get_first_non_missing(contact, ["邮箱", "email", "e-mail"])

    return phone, email


def extract_name(profile: Dict[str, Any]) -> str:
    if not isinstance(profile, dict):
        return ""
    return _get_first_non_missing(profile, ["姓名", "name", "Name"])


def extract_education(profile: Dict[str, Any]) -> str:
    """提取教育信息（满足其一即可）"""
    if not isinstance(profile, dict):
        return ""

    # 通用字段
    edu = _get_first_non_missing(profile, ["教育背景", "学历", "最高学历", "学位"])
    if edu:
        return edu

    # 研究档案：education_history 有内容也视为存在
    education_history = profile.get("education_history", [])
    if isinstance(education_history, list) and len(education_history) > 0:
        return "education_history"

    return ""


def extract_experience(profile: Dict[str, Any]) -> str:
    """提取经历信息（满足其一即可）"""
    if not isinstance(profile, dict):
        return ""

    # 工作经历列表
    work_exp = profile.get("工作经历")
    if isinstance(work_exp, list) and not is_missing(work_exp):
        return "工作经历"

    years = _get_first_non_missing(profile, ["工作年限", "年限", "experience_years", "work_years"])
    if years:
        return years

    return ""


def extract_skills(profile: Dict[str, Any]) -> str:
    """提取技能信息（满足其一即可）"""
    if not isinstance(profile, dict):
        return ""

    # 检查"技能特长"字段（支持列表或字符串格式）
    skills_value = profile.get("技能特长")
    if skills_value:
        if isinstance(skills_value, list) and not is_missing(skills_value):
            return "技能特长"
        elif isinstance(skills_value, str) and not is_missing(skills_value):
            return skills_value  # 直接返回字符串值

    # 兜底：检查其他常见字段名
    skills = _get_first_non_missing(profile, ["技能特长", "技能", "skills", "skill"])
    if skills:
        return skills

    return ""


@dataclass
class ValidationItem:
    id: str
    label: str
    ok: bool
    value: str = ""


def _build_result(
    schema: str,
    required_items: List[ValidationItem],
    recommended_items: Optional[List[ValidationItem]] = None,
    issues: Optional[List[str]] = None,
) -> Dict[str, Any]:
    missing_required = [it.label for it in required_items if not it.ok]
    missing_recommended = [it.label for it in (recommended_items or []) if not it.ok]
    return {
        "schema": schema,
        "is_complete": len(missing_required) == 0,
        "items_required": [it.__dict__ for it in required_items],
        "items_recommended": [it.__dict__ for it in (recommended_items or [])],
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
        "issues": issues or [],
    }


def validate_general_profile(profile_data: Any) -> Dict[str, Any]:
    """
    通用个人信息完整性校验（个人版/多人版成员）：
    必填：
    - 姓名
    - 电话（必填；多人版以电话为主键做去重）
    - 教育（教育背景/学历/最高学历/学位 或 education_history）
    - 经历（工作经历 或 工作年限）
    - 技能（技能特长 或 技能）
    """
    issues: List[str] = []

    if isinstance(profile_data, list):
        # 个人版文件上传可能是多行表：默认不判定为“单个个人画像”
        if len(profile_data) == 1 and isinstance(profile_data[0], dict):
            profile = profile_data[0]
            issues.append("检测到表格数据（1 行），已按单人记录校验")
        else:
            issues.append(f"检测到表格数据（{len(profile_data)} 行），个人版建议只存 1 人；请切换多人版导入")
            return _build_result(
                "general",
                required_items=[
                    ValidationItem("name", "姓名", False),
                    ValidationItem("contact", "电话或邮箱", False),
                    ValidationItem("education", "教育背景/学历", False),
                    ValidationItem("experience", "工作经历/年限", False),
                    ValidationItem("skills", "技能特长/技能", False),
                ],
                recommended_items=[],
                issues=issues,
            )

    if not isinstance(profile_data, dict):
        issues.append("画像数据结构异常（非 dict）")
        return _build_result(
            "general",
            required_items=[
                ValidationItem("name", "姓名", False),
                ValidationItem("contact", "电话或邮箱", False),
                ValidationItem("education", "教育背景/学历", False),
                ValidationItem("experience", "工作经历/年限", False),
                ValidationItem("skills", "技能特长/技能", False),
            ],
            recommended_items=[],
            issues=issues,
        )

    profile = profile_data

    name = extract_name(profile)
    phone, email = extract_contact(profile)
    education = extract_education(profile)
    experience = extract_experience(profile)
    skills = extract_skills(profile)

    required_items = [
        ValidationItem("name", "姓名", ok=not is_missing(name), value=name),
        ValidationItem("phone", "电话（必填）", ok=not is_missing(phone), value=phone),
        ValidationItem("education", "教育背景/学历", ok=not is_missing(education), value=education),
        ValidationItem("experience", "工作经历/年限", ok=not is_missing(experience), value=experience),
        ValidationItem("skills", "技能特长/技能", ok=not is_missing(skills), value=skills),
    ]

    # 推荐项（不阻断，但用于提示）
    strengths = _get_first_non_missing(profile, ["个人优势", "优势"])
    goals = _get_first_non_missing(profile, ["未来规划", "规划", "目标"])

    recommended_items = [
        ValidationItem("strengths", "个人优势（推荐）", ok=not is_missing(strengths), value=strengths[:60]),
        ValidationItem("goals", "未来规划（推荐）", ok=not is_missing(goals), value=goals[:60]),
    ]

    return _build_result("general", required_items, recommended_items, issues=issues)


def validate_research_profile(profile_data: Any) -> Dict[str, Any]:
    """
    科研档案完整性校验（用于科研表单输出阻断）：
    必填：
    - 姓名
    - 电话/邮箱（二选一）
    - 教育（education_history 至少 1 条 或 最高学历/教育背景）
    """
    issues: List[str] = []

    if not isinstance(profile_data, dict):
        issues.append("科研档案结构异常（非 dict）")
        required_items = [
            ValidationItem("name", "姓名", False),
            ValidationItem("contact", "电话或邮箱", False),
            ValidationItem("education", "教育经历/最高学历", False),
        ]
        return _build_result("research", required_items, [], issues=issues)

    profile = profile_data
    name = extract_name(profile)
    phone, email = extract_contact(profile)
    education = extract_education(profile)

    required_items = [
        ValidationItem("name", "姓名", ok=not is_missing(name), value=name),
        ValidationItem("contact", "电话或邮箱", ok=not (is_missing(phone) and is_missing(email)), value=(phone or email)),
        ValidationItem("education", "教育经历/最高学历", ok=not is_missing(education), value=education),
    ]

    return _build_result("research", required_items, [], issues=issues)

