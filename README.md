# 🧠 Digital Twin - 数字分身

> 基于 LLM 的智能表单填写与人员管理系统

一个功能强大的 Python Web 应用，帮助个人和团队快速管理数字档案、智能填写表单、追踪绩效贡献。通过 AI 技术，自动识别表单字段、生成专业答案，大幅提升工作效率。

---

## ✨ 核心功能

### 📋 数据管理
- **个人版**：管理个人数字档案，支持多种导入方式（CSV/Excel/PDF/文本分析）
- **多人版**：组织级人员管理，支持小组分组、成员去重、组内信息管理
- **统一数据源**：个人版与多人版数据统一存储，个人版自动同步到组织库

### 🪄 智能填表
- **多格式支持**：Excel、Word、纯文本问题列表
- **AI 字段识别**：自动识别表单中的字段名称
- **智能填充**：基于个人档案自动生成专业答案
- **批量处理**：支持多人批量填写，可选择"每人一份"或"汇总对照表"模式
- **语言润色**：支持专业、学术、友好三种风格

### 📚 科研表单
- **科研档案管理**：专门的科研人员信息模型（论文数、项目数等）
- **批量生成**：支持批量生成科研项目申报书
- **汇总生成**：将多人信息汇总到一张表格
- **预算校验**：自动检查项目预算是否合理

### 📈 绩效与贡献管理（新增）
- **绩效追踪**：记录基准分、贡献分、手动调整
- **贡献管理**：记录主要贡献及对应分值
- **事件历史**：完整的绩效变化审计日志
- **团队排行榜**：可视化团队绩效对比（柱状图 + 表格）
- **导入支持**：从 CSV/Excel 导入绩效和贡献数据

---

## 🛠️ 技术栈

- **Web 框架**：Streamlit 1.28+
- **数据处理**：Pandas 2.0+
- **AI 服务**：DeepSeek API / OpenAI API（兼容）
- **文件处理**：
  - Excel：openpyxl
  - Word：python-docx
  - PDF：PyMuPDF + EasyOCR（OCR 支持）
- **数据存储**：JSON（本地文件）

---

## 📦 安装与运行

### 环境要求
- Python 3.9+
- 网络连接（用于调用 AI API）

### 安装步骤

1. **克隆或下载项目**
```bash
cd vibecoding
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **运行应用**
```bash
streamlit run app.py
```

4. **访问应用**
- 浏览器自动打开，或手动访问：http://localhost:8501

### 首次使用

1. **配置 API Key**
   - 在左侧边栏输入你的 DeepSeek API Key 或 OpenAI API Key
   - API Key 会保存在 session 中，刷新页面需要重新输入

2. **选择模式**
   - **个人版**：管理个人数字档案
   - **多人版**：管理团队人员信息

3. **导入数据**
   - 支持 CSV/Excel 文件上传
   - 支持 PDF 简历上传（自动 OCR）
   - 支持文本分析（AI 提取个人信息）

---

## 📖 使用指南

### 个人版使用流程

1. **导入个人信息**
   - 方式一：上传 CSV/Excel 文件
   - 方式二：上传 PDF 简历
   - 方式三：粘贴文本，AI 自动分析

2. **查看档案**
   - 在"数据管理"页面查看个人信息完整性
   - 查看原始 JSON 数据

3. **智能填表**
   - 上传空白表单（Excel/Word）或输入问题列表
   - AI 自动识别字段
   - 一键生成答案
   - 可手动编辑后导出

4. **绩效管理**
   - 查看当前绩效、基准分、贡献累计
   - 添加主要贡献
   - 手动调整绩效
   - 查看事件历史

### 多人版使用流程

1. **创建小组**
   - 在"小组管理"标签页创建新小组

2. **导入成员**
   - 上传多人 CSV/Excel 表格
   - 系统自动去重（按电话/邮箱）
   - 可选择导入绩效和贡献数据

3. **管理成员**
   - **组织视角**：查看所有人员，搜索、筛选
   - **小组视角**：查看小组内成员，管理组内信息
   - 支持人员在不同小组间移动

4. **智能填表（多人）**
   - 选择单个或多个人员
   - 支持按团队选择
   - 生成"每人一份"或"汇总对照表"

5. **绩效管理**
   - 在人员详情页查看绩效面板
   - 查看团队绩效排行榜
   - 导出团队绩效 CSV

---

## 📁 项目结构

```
vibecoding/
├── app.py                      # Streamlit 主入口（页面编排）
├── smart_form_filler.py        # 智能填表功能
├── research_extension.py        # 科研表单功能
├── form_generator.py           # 模板填充引擎
├── pdf_resume_import.py        # PDF 简历提取
│
├── store_single.py             # 个人版存储层
├── store_org.py                # 多人版存储层（OrgStore v3）
├── self_config.py              # 身份绑定层
├── performance_models.py       # 绩效模型层
├── research_models.py          # 科研模型层
├── profile_validation.py       # 信息完整性校验
├── ai_services.py              # AI 服务封装
│
├── ui_*.py                     # UI 组件模块
│   ├── ui_sidebar.py           # 侧边栏
│   ├── ui_import.py            # 导入流程
│   ├── ui_data_management.py   # 数据管理页
│   ├── ui_performance.py        # 绩效面板
│   ├── ui_profile.py           # 档案展示
│   └── ui_common.py            # 通用组件
│
├── user_profile.json           # 个人版数据（兼容镜像）
├── user_profiles_multi.json   # 多人版数据（主数据源）
├── self_config.json            # 身份绑定配置
│
├── test_data/                  # 测试数据
│   ├── team_5_members.xlsx     # 团队数据示例
│   ├── blank_job_application.xlsx  # 空白表单示例
│   └── ...
│
├── requirements.txt            # Python 依赖
├── CODE_STRUCTURE.md          # 代码结构文档
├── PERFORMANCE_CONTRIBUTION_PLAN.md  # 绩效功能设计文档
└── README.md                   # 本文件
```

---

## 🎯 主要特性

### 1. 统一数据模型
- **个人版 = 多人版中的"我"**：个人版数据自动同步到组织库
- **去重机制**：按电话（优先）/邮箱（兜底）自动去重
- **Schema 版本管理**：自动迁移旧版本数据

### 2. 智能字段识别
- AI 自动识别表单字段（支持中英文）
- 区分事实类字段（姓名、电话）和主观类字段（个人优势、未来规划）
- 支持自定义字段映射

### 3. 批量处理优化
- **批量 AI 生成**：一次 API 调用生成所有字段答案，大幅提升速度
- **多人模式**：支持选择单个/多个/团队进行批量填写
- **输出模式**：每人一份独立表格，或汇总到一张对照表

### 4. 绩效与贡献系统
- **事件驱动模型**：所有绩效变化记录为事件，可追溯
- **多维度视图**：支持全局视角和小组视角
- **灵活导入**：支持导入基准分、贡献列表
- **可视化展示**：团队排行榜、柱状图、CSV 导出

### 5. 信息完整性校验
- **必填字段检查**：通用档案和科研档案两套规则
- **阻断机制**：信息不完整时阻止表单生成
- **清晰提示**：明确显示缺失的必填字段

---

## 💾 数据模型

### OrgStore v3 结构

```json
{
  "_schema_version": 3,
  "org": {
    "id": "org_default",
    "name": "大团队",
    "created_at": "2025-01-01 10:00:00",
    "updated_at": "2025-01-01 10:00:00"
  },
  "groups": [
    {
      "id": "g1",
      "name": "项目A组",
      "description": "",
      "tags": [],
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "people": [
    {
      "id": "p1",
      "name": "张三",
      "phone": "13812345678",
      "email": "zhangsan@example.com",
      "dedup": {
        "strategy": "phone_then_email",
        "key": "phone:13812345678"
      },
      "profile": {
        "姓名": "张三",
        "电话": "13812345678",
        "学历": "硕士",
        "工作经历": "...",
        "技能特长": "Python, 机器学习"
      },
      "memberships": [
        {
          "group_id": "g1",
          "joined_at": "2025-01-01",
          "updated_at": "2025-01-01",
          "fields": {
            "role": "组长",
            "department": "研发部"
          }
        }
      ],
      "performance": {
        "base_score": 85.0,
        "events": [
          {
            "id": "e_abc123",
            "type": "contribution",
            "delta": 20.0,
            "title": "主导XX项目上线",
            "note": "",
            "group_id": "g1",
            "at": "2025-06-01"
          }
        ],
        "updated_at": "2025-07-01 10:00:00"
      }
    }
  ]
}
```

### 绩效计算规则

- **当前绩效** = `base_score` + `sum(events[].delta)`
- **贡献累计** = `sum(type=contribution 的 events[].delta)`
- **事件类型**：
  - `import_base`：导入基准分
  - `contribution`：主要贡献
  - `manual_adjust`：手动调整

---

## 🔧 开发指南

### 代码分层架构

1. **Store（存储层）**：数据读写、迁移、去重
2. **Domain Models（领域模型层）**：纯函数、数据结构、计算逻辑
3. **Service（服务层）**：外部能力封装（AI API）
4. **Validation（校验层）**：信息完整性规则
5. **UI Components（UI 组件层）**：可复用界面组件
6. **Feature Modules（功能模块层）**：业务功能实现

### 常见修改场景

- **调整必填字段**：修改 `profile_validation.py`
- **修改去重策略**：修改 `store_org.py` 的 `_compute_dedup_key()`
- **更换 AI 模型**：修改 `ai_services.py` 的 `DEFAULT_MODEL`
- **新增表单格式**：在 `smart_form_filler.py` 添加处理逻辑
- **修改绩效计算规则**：修改 `performance_models.py`

详细架构说明请参考 [CODE_STRUCTURE.md](CODE_STRUCTURE.md)

---

## 📝 测试数据

项目包含完整的测试数据示例：

- `test_data/team_5_members.xlsx`：5 人团队数据（含绩效/贡献）
- `test_data/blank_job_application.xlsx`：空白求职申请表
- `test_data/blank_team_summary.xlsx`：空白团队汇总表
- `test_data/blank_research_proposal.xlsx`：空白科研申报书
- `test_data/个人档案_李明.csv`：个人档案示例
- `test_data/科研团队表_3人.csv`：科研团队示例

运行 `test_data/generate_test_data.py` 可重新生成测试数据。

---

## 🚀 性能优化

- **批量 AI 生成**：将多个字段的生成合并为一次 API 调用，减少网络延迟
- **懒加载**：按需加载数据，避免一次性加载大量数据
- **去重优化**：使用电话/邮箱作为去重键，O(1) 查找

---

## ⚠️ 注意事项

1. **API Key 安全**：API Key 仅保存在 session 中，不会持久化到文件
2. **数据备份**：重要数据请定期备份 `user_profiles_multi.json`
3. **必填字段**：电话是必填字段（用于去重），导入时请确保包含
4. **文件编码**：CSV/Excel 文件请使用 UTF-8 编码
5. **PDF OCR**：扫描版 PDF 需要 OCR，处理时间较长

## 🔧 故障排除

### PDF 导入失败

如果遇到 "缺少依赖：PyMuPDF" 错误：

1. **检查依赖是否安装**：
   ```bash
   python test_pdf_import.py
   ```

2. **安装 PyMuPDF**：
   ```bash
   pip install pymupdf
   ```

3. **如果仍然失败**：
   - 确保使用的是正确的 Python 环境
   - 尝试重新安装：`pip uninstall pymupdf && pip install pymupdf`
   - 检查 Python 版本（需要 Python 3.9+）

4. **使用诊断工具**：
   ```bash
   python test_pdf_import.py
   ```
   这会检查所有 PDF 相关依赖并测试功能是否正常。

### 其他常见问题

- **导入 CSV/Excel 失败**：检查文件编码，尝试另存为 UTF-8 格式
- **AI 分析失败**：检查 API Key 是否正确，网络是否正常
- **性能问题**：大量数据导入时可能需要等待，请耐心

---

## 📄 许可证

本项目为内部使用项目，未经授权不得外传。

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📞 联系方式

如有问题或建议，请通过 Issue 反馈。

---

**最后更新**：2025-02-06

**版本**：v3.0（支持绩效与贡献管理）
