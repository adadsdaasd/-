## 绩效评价与主要贡献功能改造计划（OrgStore v2）

本文件记录“为每个人新增绩效评价 + 主要贡献（贡献对应绩效）”的一套**可维护、可扩展、可审计**的工程化方案。

---

### 0) 背景与目标

你当前的多人版主数据源为 `user_profiles_multi.json`（OrgStore v2），并通过：

- `store_org.py`：组织/小组/人员/组内信息（memberships）存储层
- `ui_import.py`：导入入口
- `ui_data_management.py`：人员库/小组视角展示与编辑

现在要新增：

- **绩效评价（Performance）**：可导入当前绩效，也可不导入；不导入则初始为 0；后续支持手动调整
- **主要贡献（Contributions）**：每人可记录多条贡献；每条贡献对应一个绩效分值（加分/扣分）
- **多人/小组维度**：既能在“组织视角”看全局，也能在“小组视角”看本组贡献与绩效
- **工程化**：结构清晰、便于未来修改口径（按月/季度、按组、权重、审批等）

---

### 1) 需求拆解（功能清单）

- **导入阶段**
  - **可选**导入“当前绩效”（可从 CSV/Excel 列读取）
  - 不导入时：新成员初始绩效为 **0**
  - 允许表格同时带“主要贡献”与“贡献分值”

- **后续维护**
  - 手动新增/编辑/删除绩效事件
  - 手动新增/编辑/删除主要贡献（贡献 = 一类绩效事件）

- **展示与输出**
  - 人员详情页显示：当前绩效、贡献列表、历史调整
  - 小组视角默认显示：该组内贡献/绩效（可切换为全局）
  - 团队绩效看板（后续迭代）：排行榜、柱状图、导出 CSV

---

### 2) 设计原则（工程化约束）

- **Single Source of Truth**：绩效的唯一真相在 OrgStore（`user_profiles_multi.json`）
- **可审计**：绩效变化必须可追溯（何时/因何/加减多少/归属小组）
- **弱耦合**：UI 只负责交互；存储层负责读写与一致性；模型层负责计算与校验
- **可扩展**：未来扩展到“月度/季度绩效、审批、权重、按组统计”不推翻数据结构

---

### 3) 数据模型（推荐：事件流水模型，最稳）

#### 3.1 在 person 上新增 `performance`

在 `store_org.py` 的 `people[]` 每个 `person` 中新增：

- `performance.base_score`: 初始/当前基准分（默认 0）
- `performance.events`: 绩效事件列表（贡献/导入/手动调整均用事件表达）
- `performance.updated_at`: 最后更新时间

示例（简化）：

```json
{
  "id": "p1",
  "name": "李明",
  "phone": "138...",
  "profile": { "...": "..." },
  "memberships": [ { "group_id": "g1", "fields": { "role": "组长" } } ],
  "performance": {
    "base_score": 0,
    "events": [
      {
        "id": "e_import_001",
        "type": "import_base",
        "delta": 60,
        "title": "导入当前绩效",
        "note": "来自Excel列: 当前绩效",
        "group_id": null,
        "at": "2026-02-06"
      },
      {
        "id": "e_contrib_001",
        "type": "contribution",
        "delta": 5,
        "title": "主导CTR模型升级",
        "note": "点击率+15%",
        "group_id": "g1",
        "at": "2026-01-15"
      }
    ],
    "updated_at": "2026-02-06 21:00:00"
  }
}
```

#### 3.2 绩效口径（默认）

- **当前绩效分** = `base_score + sum(events[].delta)`
- **主要贡献** = `events` 中 `type="contribution"` 的子集
- 支持负分（扣分/回滚/纠偏）

#### 3.3 为什么不把绩效放进 `profile`/`membership.fields`

- `profile` 面向“画像信息”，字段松散且多来源；绩效是强结构、需要统计与审计的数据
- `membership.fields` 面向“组内信息”，更适合 role/task 等；绩效既有全局也有按组维度

因此采用 `person.performance` 作为绩效域的稳定落点。

---

### 4) 分层与文件改动建议（便于维护）

新增/改造按职责拆分：

#### 4.1 模型层（新建）

新增文件：`performance_models.py`（纯函数，不依赖 Streamlit）

建议包含：

- `parse_score(value) -> float`
- `ensure_performance(perf) -> perf`
- `compute_current_score(perf) -> float`
- `filter_events(perf, group_id=None, event_type=None, date_range=None) -> list`
- `build_contribution_event(title, delta, note, group_id, at) -> dict`

#### 4.2 存储层（扩展）

在 `store_org.py` 新增 API（只做数据读写与一致性）：

- `ensure_person_performance(person: dict) -> None`
- `get_person_performance(person_id) -> dict`
- `set_person_base_score(person_id, base_score, note=None) -> bool`
- `add_performance_event(person_id, event: dict) -> bool`
- `update_performance_event(person_id, event_id, patch: dict) -> bool`
- `delete_performance_event(person_id, event_id) -> bool`
- `get_person_performance_summary(person_id, group_id=None) -> dict`

#### 4.3 UI 层（新增可复用组件）

新增文件：`ui_performance.py`

- `render_performance_panel(person: dict, context_group_id: str | None = None)`
  - 摘要指标（base/current/贡献累计/事件数）
  - 添加主要贡献表单
  - 手动调整表单
  - 事件表格（data_editor）+ 删除/编辑入口

在 `ui_data_management.py`：

- 在 `_render_person_detail_org_view()` 引入 `render_performance_panel(person, context_group_id=None)`
- 在 `_render_person_detail_group_view()` 引入 `render_performance_panel(person, context_group_id=group_id)`（默认按组过滤）

#### 4.4 导入层（扩展）

在 `ui_import.py` 的多人批量导入设置区增加：

- 导入绩效策略（radio）：
  - `ignore`：忽略绩效列（新成员 base=0）
  - `new_only`：仅新成员写入 base
  - `overwrite`：覆盖 base 并追加事件记录

- 贡献解析（可选 checkbox）：
  - 解析“主要贡献”与“贡献分值”列
  - 或支持“单元格多贡献”格式：`贡献A|5; 贡献B|3`

---

### 5) Schema 迁移（保证老数据不崩）

当前 `store_org.py` 的 `SCHEMA_VERSION = 2`。

建议升级到 v3：

- 对每个 `person`：
  - 如果不存在 `performance`，补：
    - `base_score = 0`
    - `events = []`
    - `updated_at = now`

迁移触发点：在 `load_org_store()` 读取到旧版本时自动迁移并保存。

---

### 6) 导入策略细节（满足“可选导入绩效/默认0”）

#### 6.1 绩效列识别（容错）

候选列名：

- `["当前绩效","绩效","绩效分","绩效评分","performance","score"]`

解析规则：

- 空/缺失：视为“不导入”
- 非数字：提示并跳过（写入 issues）

#### 6.2 不导入时的初始化

- 新成员：`base_score=0, events=[]`
- 已存在成员：保持原 `performance`（不覆盖）

#### 6.3 导入贡献（可选）

候选列名：

- 贡献文本：`["主要贡献","贡献","contribution"]`
- 贡献分值：`["贡献绩效","贡献分","contribution_score"]`

若存在贡献文本但无分值：

- 可设默认 delta（例如 0）并提示用户后续补全

---

### 7) UI 交互设计（组织视角 vs 小组视角）

#### 7.1 组织视角（人员库）

人员详情新增“绩效与贡献”卡片：

- 当前绩效（current）
- 基准分（base）
- 贡献累计（sum(contribution.delta)）
- 最近贡献/调整时间

下方：

- 添加主要贡献（title/delta/note/date/可选 group）
- 手动调整（delta/reason/date）
- 历史事件表（可筛选 type）

#### 7.2 小组视角（组内成员）

默认：

- 只显示 `group_id == 当前小组` 的事件
- 添加贡献默认带上 `group_id=当前小组`

提供切换：

- “显示全局事件”开关（用于跨组汇总）

---

### 8) 与智能填表的联动（可选增量）

在 `smart_form_filler.py` 的 profile summary 中追加：

- 当前绩效分（current）
- Top N 贡献（按 delta 或时间）

当字段包含关键词（绩效/评价/贡献/成果/亮点）时优先生成更准确、更可控的回答。

---

### 9) 测试与验收（Definition of Done）

#### 9.1 数据迁移

- 旧数据加载不报错
- 迁移后所有 person 都有 `performance` 字段且 base=0/events=[]

#### 9.2 导入验收

- 表格不含绩效列：新成员 current=0
- 含绩效列但选择 ignore：新成员 current=0
- new_only：仅新成员写入 base（老成员不变）
- overwrite：覆盖 base 并追加 import 事件（可审计）

#### 9.3 UI 验收

- 组织视角/小组视角都能查看与编辑绩效
- 新增贡献后，current 立即更新
- 删除事件后，current 回滚且 updated_at 更新

#### 9.4 统计与导出（后续）

- 团队绩效汇总可导出 CSV
- 贡献明细可导出 CSV

---

### 10) 迭代路线（建议拆 3 个小步，低风险上线）

- **Phase A（存储层 + 迁移）** ✅ 已完成
  - 新增 `performance_models.py`
  - 扩展 `store_org.py` 的绩效 API
  - SCHEMA v2 → v3 升级与自动迁移

- **Phase B（导入）** ✅ 已完成
  - `ui_import.py` 增加绩效/贡献导入策略（ignore / new_only / overwrite）
  - 导入时调用绩效 API 写入 base/events
  - 支持 "贡献A|20; 贡献B|10" 格式自动解析

- **Phase C（UI）** ✅ 已完成
  - 新增 `ui_performance.py`（完整面板：指标/贡献/调整/基准/历史/排行榜）
  - 在个人版、组织视角、小组视角三处接入绩效面板
  - 团队绩效排行榜（柱状图 + 表格 + CSV 导出）

> 所有阶段已完成实现。

