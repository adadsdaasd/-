"""
研究档案数据模型 (Research Models)
==================================
定义学术/科研相关的数据结构、存储函数和验证逻辑
"""

import json
import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any

# ==================== 常量定义 ====================

RESEARCH_PROFILES_FILE = "research_profiles.json"

# 学术档案数据结构模板
RESEARCH_PROFILE_TEMPLATE = {
    # === 基本信息（与现有系统兼容） ===
    "姓名": "",
    "联系方式": {
        "电话": "",
        "邮箱": ""
    },
    
    # === 学术专用字段 ===
    "education_history": [],      # 教育经历列表
    "publications": [],           # 论文发表列表
    "grants": [],                 # 项目/基金列表
    "budget_constraints": {       # 预算限制配置
        "labor_fee_max_ratio": 0.5,
        "equipment_fee_max_ratio": 0.3,
        "travel_fee_max_ratio": 0.1,
        "indirect_cost_ratio": 0.1
    }
}

# 教育经历模板
EDUCATION_TEMPLATE = {
    "degree": "",           # 学位：博士/硕士/学士
    "institution": "",      # 院校名称
    "major": "",            # 专业
    "start_date": "",       # 开始日期 YYYY-MM
    "end_date": ""          # 结束日期 YYYY-MM
}

# 论文发表模板
PUBLICATION_TEMPLATE = {
    "title": "",            # 论文标题
    "journal": "",          # 期刊/会议名称
    "year": None,           # 发表年份
    "doi": "",              # DOI
    "type": "",             # 类型：SCI/EI/核心/其他
    "authors": "",          # 作者列表
    "impact_factor": None   # 影响因子
}

# 项目/基金模板
GRANT_TEMPLATE = {
    "project_name": "",     # 项目名称
    "grant_id": "",         # 基金号
    "role": "",             # 角色：负责人/参与者
    "budget": 0,            # 预算金额
    "start_date": "",       # 开始日期
    "end_date": "",         # 结束日期
    "funding_agency": ""    # 资助机构
}

# 预算分配模板
BUDGET_ALLOCATION_TEMPLATE = {
    "labor_fee": 0,         # 人员费
    "equipment_fee": 0,     # 设备费
    "material_fee": 0,      # 材料费
    "travel_fee": 0,        # 差旅费
    "conference_fee": 0,    # 会议费
    "publication_fee": 0,   # 出版费
    "indirect_cost": 0,     # 间接费用
    "other_fee": 0          # 其他费用
}


# ==================== 数据存储函数 ====================

def load_research_profiles() -> List[Dict]:
    """加载所有研究档案"""
    if not os.path.exists(RESEARCH_PROFILES_FILE):
        return []
    
    try:
        with open(RESEARCH_PROFILES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, Exception):
        return []


def save_research_profiles(profiles: List[Dict]) -> bool:
    """保存所有研究档案"""
    try:
        with open(RESEARCH_PROFILES_FILE, 'w', encoding='utf-8') as f:
            json.dump(profiles, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存研究档案失败: {str(e)}")
        return False


def create_research_profile(name: str, base_profile: Optional[Dict] = None) -> Dict:
    """
    创建新的研究档案
    
    Args:
        name: 姓名
        base_profile: 可选的基础档案（从现有系统导入）
    
    Returns:
        新创建的研究档案
    """
    profile_id = str(uuid.uuid4())[:8]
    
    new_profile = {
        "id": profile_id,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **RESEARCH_PROFILE_TEMPLATE.copy()
    }
    
    new_profile["姓名"] = name
    
    # 如果有基础档案，合并数据
    if base_profile:
        if isinstance(base_profile, dict):
            # 合并基本信息
            for key in ["姓名", "联系方式", "教育背景", "工作经历", "技能特长"]:
                if key in base_profile:
                    new_profile[key] = base_profile[key]
    
    return new_profile


def add_research_profile(profile: Dict) -> bool:
    """添加研究档案到列表"""
    profiles = load_research_profiles()
    profiles.append(profile)
    return save_research_profiles(profiles)


def update_research_profile(profile_id: str, updated_data: Dict) -> bool:
    """更新指定研究档案"""
    profiles = load_research_profiles()
    
    for i, p in enumerate(profiles):
        if p.get("id") == profile_id:
            profiles[i].update(updated_data)
            profiles[i]["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            return save_research_profiles(profiles)
    
    return False


def delete_research_profile(profile_id: str) -> bool:
    """删除指定研究档案"""
    profiles = load_research_profiles()
    profiles = [p for p in profiles if p.get("id") != profile_id]
    return save_research_profiles(profiles)


def get_research_profile_by_id(profile_id: str) -> Optional[Dict]:
    """根据 ID 获取研究档案"""
    profiles = load_research_profiles()
    for p in profiles:
        if p.get("id") == profile_id:
            return p
    return None


def get_research_profile_by_name(name: str) -> Optional[Dict]:
    """根据姓名获取研究档案"""
    profiles = load_research_profiles()
    for p in profiles:
        if p.get("姓名") == name:
            return p
    return None


# ==================== 教育经历管理 ====================

def add_education(profile_id: str, education: Dict) -> bool:
    """为档案添加教育经历"""
    profile = get_research_profile_by_id(profile_id)
    if not profile:
        return False
    
    if "education_history" not in profile:
        profile["education_history"] = []
    
    # 添加唯一 ID
    education["id"] = str(uuid.uuid4())[:6]
    profile["education_history"].append(education)
    
    return update_research_profile(profile_id, profile)


def remove_education(profile_id: str, education_id: str) -> bool:
    """移除教育经历"""
    profile = get_research_profile_by_id(profile_id)
    if not profile:
        return False
    
    profile["education_history"] = [
        e for e in profile.get("education_history", [])
        if e.get("id") != education_id
    ]
    
    return update_research_profile(profile_id, profile)


# ==================== 论文管理 ====================

def add_publication(profile_id: str, publication: Dict) -> bool:
    """为档案添加论文"""
    profile = get_research_profile_by_id(profile_id)
    if not profile:
        return False
    
    if "publications" not in profile:
        profile["publications"] = []
    
    publication["id"] = str(uuid.uuid4())[:6]
    profile["publications"].append(publication)
    
    return update_research_profile(profile_id, profile)


def remove_publication(profile_id: str, publication_id: str) -> bool:
    """移除论文"""
    profile = get_research_profile_by_id(profile_id)
    if not profile:
        return False
    
    profile["publications"] = [
        p for p in profile.get("publications", [])
        if p.get("id") != publication_id
    ]
    
    return update_research_profile(profile_id, profile)


def get_publications_summary(profile: Dict) -> Dict:
    """获取论文统计摘要"""
    publications = profile.get("publications", [])
    
    summary = {
        "total": len(publications),
        "sci": 0,
        "ei": 0,
        "core": 0,
        "other": 0
    }
    
    for pub in publications:
        pub_type = pub.get("type", "").upper()
        if "SCI" in pub_type:
            summary["sci"] += 1
        elif "EI" in pub_type:
            summary["ei"] += 1
        elif "核心" in pub_type:
            summary["core"] += 1
        else:
            summary["other"] += 1
    
    return summary


# ==================== 项目/基金管理 ====================

def add_grant(profile_id: str, grant: Dict) -> bool:
    """为档案添加项目"""
    profile = get_research_profile_by_id(profile_id)
    if not profile:
        return False
    
    if "grants" not in profile:
        profile["grants"] = []
    
    grant["id"] = str(uuid.uuid4())[:6]
    profile["grants"].append(grant)
    
    return update_research_profile(profile_id, profile)


def remove_grant(profile_id: str, grant_id: str) -> bool:
    """移除项目"""
    profile = get_research_profile_by_id(profile_id)
    if not profile:
        return False
    
    profile["grants"] = [
        g for g in profile.get("grants", [])
        if g.get("id") != grant_id
    ]
    
    return update_research_profile(profile_id, profile)


def get_grants_summary(profile: Dict) -> Dict:
    """获取项目统计摘要"""
    grants = profile.get("grants", [])
    
    total_budget = sum(g.get("budget", 0) for g in grants)
    as_pi = sum(1 for g in grants if "负责人" in g.get("role", ""))
    as_member = len(grants) - as_pi
    
    return {
        "total": len(grants),
        "as_pi": as_pi,          # 作为负责人
        "as_member": as_member,  # 作为参与者
        "total_budget": total_budget
    }


# ==================== 预算验证逻辑 ====================

def validate_budget(budget_allocation: Dict, constraints: Optional[Dict] = None) -> List[str]:
    """
    验证预算分配是否符合约束
    
    Args:
        budget_allocation: 预算分配字典
        constraints: 约束条件，默认使用标准约束
    
    Returns:
        警告信息列表
    """
    if constraints is None:
        constraints = RESEARCH_PROFILE_TEMPLATE["budget_constraints"]
    
    warnings = []
    
    # 计算总预算
    total = sum(budget_allocation.values())
    if total <= 0:
        return ["错误：总预算必须大于 0"]
    
    # 检查人员费
    labor = budget_allocation.get("labor_fee", 0)
    labor_max = constraints.get("labor_fee_max_ratio", 0.5)
    if labor / total > labor_max:
        warnings.append(f"⚠️ 人员费占比 {labor/total:.1%} 超过 {labor_max:.0%} 限制")
    
    # 检查设备费
    equipment = budget_allocation.get("equipment_fee", 0)
    equipment_max = constraints.get("equipment_fee_max_ratio", 0.3)
    if equipment / total > equipment_max:
        warnings.append(f"⚠️ 设备费占比 {equipment/total:.1%} 超过 {equipment_max:.0%} 限制")
    
    # 检查差旅费
    travel = budget_allocation.get("travel_fee", 0)
    travel_max = constraints.get("travel_fee_max_ratio", 0.1)
    if travel / total > travel_max:
        warnings.append(f"⚠️ 差旅费占比 {travel/total:.1%} 超过 {travel_max:.0%} 限制")
    
    # 检查间接费用
    indirect = budget_allocation.get("indirect_cost", 0)
    indirect_expected = constraints.get("indirect_cost_ratio", 0.1)
    if abs(indirect / total - indirect_expected) > 0.02:  # 允许 2% 误差
        warnings.append(f"ℹ️ 间接费用占比 {indirect/total:.1%}，建议为 {indirect_expected:.0%}")
    
    return warnings


def calculate_budget_summary(budget_allocation: Dict) -> Dict:
    """计算预算摘要"""
    total = sum(budget_allocation.values())
    
    summary = {
        "total": total,
        "breakdown": {}
    }
    
    for key, value in budget_allocation.items():
        if total > 0:
            summary["breakdown"][key] = {
                "amount": value,
                "ratio": value / total
            }
    
    return summary


# ==================== 数据导出辅助 ====================

def flatten_profile_for_template(profile: Dict) -> Dict:
    """
    将档案扁平化，用于模板填充
    
    返回的字典可直接用于 {{placeholder}} 替换
    """
    flat = {}
    
    # 基本信息
    flat["name"] = profile.get("姓名", "")
    flat["姓名"] = profile.get("姓名", "")
    
    contact = profile.get("联系方式", {})
    flat["phone"] = contact.get("电话", "") if isinstance(contact, dict) else ""
    flat["email"] = contact.get("邮箱", "") if isinstance(contact, dict) else ""
    flat["电话"] = flat["phone"]
    flat["邮箱"] = flat["email"]
    
    # 教育信息（取最高学历）
    education_list = profile.get("education_history", [])
    if education_list:
        # 按学位排序：博士 > 硕士 > 学士
        degree_order = {"博士": 3, "硕士": 2, "学士": 1}
        sorted_edu = sorted(
            education_list,
            key=lambda x: degree_order.get(x.get("degree", ""), 0),
            reverse=True
        )
        highest = sorted_edu[0]
        flat["degree"] = highest.get("degree", "")
        flat["institution"] = highest.get("institution", "")
        flat["major"] = highest.get("major", "")
        flat["学位"] = flat["degree"]
        flat["院校"] = flat["institution"]
        flat["专业"] = flat["major"]
    
    # 论文统计
    pub_summary = get_publications_summary(profile)
    flat["publications_count"] = pub_summary["total"]
    flat["sci_count"] = pub_summary["sci"]
    flat["ei_count"] = pub_summary["ei"]
    flat["论文总数"] = pub_summary["total"]
    flat["SCI论文数"] = pub_summary["sci"]
    
    # 项目统计
    grant_summary = get_grants_summary(profile)
    flat["grants_count"] = grant_summary["total"]
    flat["grants_as_pi"] = grant_summary["as_pi"]
    flat["total_grant_budget"] = grant_summary["total_budget"]
    flat["项目总数"] = grant_summary["total"]
    flat["主持项目数"] = grant_summary["as_pi"]
    
    return flat


def get_all_profiles_for_selection() -> List[Dict]:
    """获取所有档案的简要信息，用于选择界面"""
    profiles = load_research_profiles()
    
    selection_list = []
    for p in profiles:
        pub_summary = get_publications_summary(p)
        grant_summary = get_grants_summary(p)
        
        selection_list.append({
            "id": p.get("id"),
            "name": p.get("姓名", "未知"),
            "degree": p.get("education_history", [{}])[0].get("degree", "") if p.get("education_history") else "",
            "institution": p.get("education_history", [{}])[0].get("institution", "") if p.get("education_history") else "",
            "publications": pub_summary["total"],
            "grants": grant_summary["total"]
        })
    
    return selection_list
