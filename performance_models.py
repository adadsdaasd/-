"""
绩效与贡献模型层 (Performance & Contribution Models)
=====================================================
纯函数，不依赖 Streamlit / 不做文件读写。
职责：数据结构定义、计算、过滤、校验。
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


# ==================== 常量 ====================

# 绩效列候选名（导入时识别用）
PERFORMANCE_COL_CANDIDATES = [
    "当前绩效", "绩效", "绩效分", "绩效评分", "performance", "score"
]

# 贡献列候选名
CONTRIBUTION_COL_CANDIDATES = [
    "主要贡献", "贡献", "contribution", "contributions"
]

# 贡献分值列候选名
CONTRIBUTION_SCORE_COL_CANDIDATES = [
    "贡献绩效", "贡献分", "contribution_score"
]

# 事件类型
EVENT_TYPE_IMPORT = "import_base"
EVENT_TYPE_CONTRIBUTION = "contribution"
EVENT_TYPE_MANUAL_ADJUST = "manual_adjust"


# ==================== 工具函数 ====================

def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _today() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def _new_event_id() -> str:
    return f"e_{uuid.uuid4().hex[:8]}"


# ==================== 数据结构 ====================

def empty_performance() -> Dict[str, Any]:
    """创建空的 performance 结构（base=0, 无事件）"""
    return {
        "base_score": 0.0,
        "events": [],
        "updated_at": _now(),
    }


def ensure_performance(person: Dict[str, Any]) -> Dict[str, Any]:
    """
    确保 person 拥有合法的 performance 字段。
    若缺失/格式异常则补齐，返回 person（原地修改）。
    """
    perf = person.get("performance")
    if not isinstance(perf, dict):
        person["performance"] = empty_performance()
    else:
        if "base_score" not in perf:
            perf["base_score"] = 0.0
        if not isinstance(perf.get("events"), list):
            perf["events"] = []
        if "updated_at" not in perf:
            perf["updated_at"] = _now()
    return person


# ==================== 分值解析 ====================

def parse_score(value: Any) -> Optional[float]:
    """
    把各种来源的值解析为 float 分数。
    无法解析则返回 None。
    """
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        s = value.strip()
        if not s or s.lower() in ("", "无", "未提及", "none", "null", "n/a", "na"):
            return None
        # 去掉可能的"分"字
        s = s.replace("分", "").strip()
        try:
            return float(s)
        except ValueError:
            return None
    return None


# ==================== 计算 ====================

def compute_current_score(perf: Dict[str, Any]) -> float:
    """当前绩效分 = base_score + sum(events[].delta)"""
    base = float(perf.get("base_score", 0))
    total_delta = sum(float(e.get("delta", 0)) for e in perf.get("events", []))
    return base + total_delta


def compute_contribution_total(perf: Dict[str, Any]) -> float:
    """贡献累计分 = sum(type=contribution 的 delta)"""
    return sum(
        float(e.get("delta", 0))
        for e in perf.get("events", [])
        if e.get("type") == EVENT_TYPE_CONTRIBUTION
    )


def count_contributions(perf: Dict[str, Any]) -> int:
    """贡献条目数"""
    return sum(1 for e in perf.get("events", []) if e.get("type") == EVENT_TYPE_CONTRIBUTION)


def get_summary(perf: Dict[str, Any], group_id: Optional[str] = None) -> Dict[str, Any]:
    """
    绩效摘要（可按 group 过滤）。
    返回: {base, current, contribution_total, contribution_count, event_count, last_updated}
    """
    events = perf.get("events", [])
    if group_id:
        events = [e for e in events if e.get("group_id") == group_id or e.get("group_id") is None]

    base = float(perf.get("base_score", 0))
    total_delta = sum(float(e.get("delta", 0)) for e in events)
    contrib_delta = sum(float(e.get("delta", 0)) for e in events if e.get("type") == EVENT_TYPE_CONTRIBUTION)
    contrib_count = sum(1 for e in events if e.get("type") == EVENT_TYPE_CONTRIBUTION)

    return {
        "base_score": base,
        "current_score": base + total_delta,
        "contribution_total": contrib_delta,
        "contribution_count": contrib_count,
        "event_count": len(events),
        "last_updated": perf.get("updated_at", ""),
    }


# ==================== 过滤 ====================

def filter_events(
    perf: Dict[str, Any],
    group_id: Optional[str] = None,
    event_type: Optional[str] = None,
) -> List[Dict]:
    """
    过滤事件列表。
    - group_id: 仅保留该 group 或 group_id=None（全局事件）
    - event_type: 仅保留该类型
    """
    events = perf.get("events", [])
    if group_id is not None:
        events = [e for e in events if e.get("group_id") == group_id or e.get("group_id") is None]
    if event_type is not None:
        events = [e for e in events if e.get("type") == event_type]
    return events


def get_contributions(perf: Dict[str, Any], group_id: Optional[str] = None) -> List[Dict]:
    """获取主要贡献列表"""
    return filter_events(perf, group_id=group_id, event_type=EVENT_TYPE_CONTRIBUTION)


# ==================== 事件构建 ====================

def build_event(
    event_type: str,
    delta: float,
    title: str,
    note: str = "",
    group_id: Optional[str] = None,
    at: Optional[str] = None,
) -> Dict[str, Any]:
    """构建一个绩效事件"""
    return {
        "id": _new_event_id(),
        "type": event_type,
        "delta": float(delta),
        "title": title,
        "note": note,
        "group_id": group_id,
        "at": at or _today(),
    }


def build_contribution_event(
    title: str,
    delta: float,
    note: str = "",
    group_id: Optional[str] = None,
    at: Optional[str] = None,
) -> Dict[str, Any]:
    """构建一条主要贡献事件"""
    return build_event(EVENT_TYPE_CONTRIBUTION, delta, title, note, group_id, at)


def build_import_event(
    delta: float,
    note: str = "导入当前绩效",
) -> Dict[str, Any]:
    """构建一条导入事件"""
    return build_event(EVENT_TYPE_IMPORT, delta, note)


def build_manual_adjust_event(
    delta: float,
    title: str,
    note: str = "",
    group_id: Optional[str] = None,
) -> Dict[str, Any]:
    """构建一条手动调整事件"""
    return build_event(EVENT_TYPE_MANUAL_ADJUST, delta, title, note, group_id)


# ==================== 导入解析 ====================

def detect_performance_col(columns: List[str]) -> Optional[str]:
    """从 DataFrame 列名中识别绩效列"""
    for col in columns:
        col_lower = col.strip().lower()
        for candidate in PERFORMANCE_COL_CANDIDATES:
            if candidate.lower() == col_lower or candidate.lower() in col_lower:
                return col
    return None


def detect_contribution_cols(columns: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    从 DataFrame 列名中识别贡献列和贡献分值列。
    返回: (contrib_col, contrib_score_col)
    """
    contrib_col = None
    score_col = None

    for col in columns:
        col_lower = col.strip().lower()
        for candidate in CONTRIBUTION_COL_CANDIDATES:
            if candidate.lower() == col_lower or candidate.lower() in col_lower:
                contrib_col = col
                break
        for candidate in CONTRIBUTION_SCORE_COL_CANDIDATES:
            if candidate.lower() == col_lower or candidate.lower() in col_lower:
                score_col = col
                break

    return contrib_col, score_col


def parse_contributions_text(text: str, default_delta: float = 0.0) -> List[Dict]:
    """
    解析单元格文本中的多条贡献。
    支持格式：
      - "贡献A|5; 贡献B|3"（竖线分隔分值，分号分隔多条）
      - "贡献A; 贡献B"（无分值，使用默认 delta）
      - "贡献A"（单条）
    """
    if not text or not isinstance(text, str):
        return []

    text = text.strip()
    if not text:
        return []

    results = []
    # 按分号拆分
    items = [s.strip() for s in text.replace("；", ";").split(";") if s.strip()]

    for item in items:
        if "|" in item:
            parts = item.rsplit("|", 1)
            title = parts[0].strip()
            delta = parse_score(parts[1]) if len(parts) > 1 else default_delta
            if delta is None:
                delta = default_delta
        else:
            title = item.strip()
            delta = default_delta

        if title:
            results.append(build_contribution_event(title=title, delta=delta))

    return results
