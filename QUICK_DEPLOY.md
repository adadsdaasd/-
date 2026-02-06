# 快速部署指南

## 概述

本指南帮助您快速部署 Digital Twin 到多用户环境，实现：
- ✅ 多人版数据共享（所有人看到相同数据）
- ✅ 个人版数据独立（每个人绑定自己的身份）

---

## 快速开始（5分钟）

### 步骤 1：管理员设置共享数据（1分钟）

1. **创建共享文件夹**
   ```
   例如：\\server\shared\digital_twin
   或：C:\SharedData\DigitalTwin
   ```

2. **运行管理员设置工具**
   ```bash
   python deploy_setup.py --admin
   ```
   按提示输入共享文件夹路径

3. **完成！** 配置文件已创建在共享文件夹中

### 步骤 2：用户本地设置（2分钟）

**方式一：使用配置文件（推荐）**
```bash
python deploy_setup.py --user --config \\server\shared\digital_twin\deployment_config.json
```

**方式二：使用启动脚本**
1. 编辑 `start_app.bat`（Windows）或 `start_app.sh`（Linux）
2. 修改 `DIGITAL_TWIN_SHARED_DIR` 为共享路径
3. 运行启动脚本

**方式三：手动设置环境变量**
```bash
# Windows
set DIGITAL_TWIN_SHARED_DIR=\\server\shared\digital_twin
streamlit run app.py

# Linux/Mac
export DIGITAL_TWIN_SHARED_DIR="/mnt/shared/digital_twin"
streamlit run app.py
```

### 步骤 3：启动应用（1分钟）

```bash
streamlit run app.py
```

### 步骤 4：首次使用（1分钟）

1. **绑定个人身份**（个人版）
   - 切换到「个人版」模式
   - 点击「绑定我是谁」
   - 输入姓名搜索并绑定

2. **或直接使用多人版**
   - 切换到「多人版」模式
   - 查看团队数据

---

## 文件说明

### 核心文件

- `config_paths.py` - 路径配置管理（自动识别共享/本地路径）
- `deploy_setup.py` - 部署设置工具
- `start_app.bat` / `start_app.sh` - 启动脚本
- `deployment_config.json` - 配置文件（自动生成）

### 数据文件

**共享位置**（所有人共用）：
- `user_profiles_multi.json` - 多人版数据

**本地位置**（每个用户独立）：
- `self_config.json` - 个人绑定配置
- `user_profile.json` - 个人版数据镜像（可选）

---

## 配置方式对比

| 方式 | 优点 | 适用场景 |
|------|------|----------|
| 部署工具 | 简单、自动化 | 推荐，适合大多数用户 |
| 启动脚本 | 一键启动 | 适合固定环境 |
| 环境变量 | 灵活 | 适合临时测试 |

---

## 常见问题

### Q: 如何修改共享路径？

**A:** 三种方式：
1. 重新运行 `deploy_setup.py --user`
2. 修改 `deployment_config.json` 文件
3. 修改启动脚本中的环境变量

### Q: 多个用户同时修改会冲突吗？

**A:** 
- 多人版数据：最后写入生效（建议重要操作前刷新）
- 个人版数据：通过 `self_person_id` 隔离，不会冲突

### Q: 如何备份数据？

**A:** 备份共享文件夹中的 `user_profiles_multi.json` 文件即可

### Q: 个人配置在哪里？

**A:** 默认在 `%USERPROFILE%\DigitalTwin`（Windows）或 `~/DigitalTwin`（Linux/Mac）

---

## 下一步

详细部署计划请参考：`DEPLOYMENT_PLAN.md`
