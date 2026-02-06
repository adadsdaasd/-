# 本地部署计划文档

## 目标

实现多用户本地部署，满足以下需求：
- **多人版数据共享**：所有用户看到相同的组织/团队/人员数据
- **个人版数据独立**：每个用户绑定自己的身份，可以独立修改个人信息

---

## 架构设计

### 数据存储结构

```
共享位置（网络驱动器/共享文件夹）
├── user_profiles_multi.json    # 多人版数据（共享，所有人读写）
└── shared_config.json           # 共享配置（可选）

用户本地目录（每个用户独立）
├── self_config.json             # 个人绑定配置（self_person_id）
└── user_profile.json            # 个人版数据镜像（可选，兼容）
```

### 数据流向

```
┌─────────────────────────────────────────────────────────┐
│           共享数据（user_profiles_multi.json）          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 组织/小组/人员/绩效（所有人共享，统一管理）      │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                    ▲                    │
                    │                    │
        ┌───────────┴──────────┐        │
        │                       │        │
┌───────┴──────┐      ┌────────┴──────┐ │
│  用户A本地   │      │  用户B本地    │ │
│              │      │              │ │
│ self_config  │      │ self_config  │ │
│ (绑定p1)     │      │ (绑定p2)     │ │
│              │      │              │ │
│ 读取共享数据 │      │ 读取共享数据  │ │
│ 修改p1信息  │      │ 修改p2信息   │ │
│ 写入共享数据 │      │ 写入共享数据 │ │
└──────────────┘      └──────────────┘ │
        │                       │        │
        └───────────┬──────────┘        │
                    │                    │
                    ▼                    ▼
        个人版修改 → 同步到共享数据 ← 多人版修改
```

---

## 实现方案

### 方案一：环境变量配置（推荐）

**优点**：灵活、易于管理、无需修改代码逻辑

**实现步骤**：

1. **创建配置文件模块** (`config_paths.py`)
   - 读取环境变量或配置文件
   - 提供数据文件路径的获取函数

2. **修改存储层**
   - `store_org.py`：支持可配置的多人版数据路径
   - `self_config.py`：支持可配置的个人配置路径

3. **部署配置**
   - 每个用户设置环境变量指向共享位置
   - 个人配置自动保存在本地

### 方案二：配置文件驱动

**优点**：集中管理、易于版本控制

**实现步骤**：

1. **创建部署配置文件** (`deployment_config.json`)
   ```json
   {
     "shared_data_path": "\\\\server\\shared\\digital_twin",
     "local_config_path": "%USERPROFILE%\\DigitalTwin",
     "mode": "shared"
   }
   ```

2. **修改存储层支持路径配置**
   - 读取配置文件
   - 动态设置数据文件路径

### 方案三：启动参数配置

**优点**：简单直接、无需环境变量

**实现步骤**：

1. **修改 `app.py`**
   - 添加命令行参数解析
   - 支持 `--shared-path` 和 `--local-path` 参数

2. **启动脚本**
   - 为每个用户创建启动脚本
   - 脚本中指定共享路径

---

## 推荐方案：环境变量 + 配置文件混合

结合方案一和方案二的优势，提供灵活的配置方式。

---

## 详细实现计划

### Phase 1: 创建配置管理模块

**文件**：`config_paths.py`

```python
"""
数据路径配置管理
================
支持环境变量和配置文件两种方式配置数据存储路径。
"""

import os
import json
from pathlib import Path
from typing import Optional

# 默认配置
DEFAULT_SHARED_DATA_FILE = "user_profiles_multi.json"
DEFAULT_SELF_CONFIG_FILE = "self_config.json"
DEFAULT_USER_PROFILE_FILE = "user_profile.json"

# 环境变量名
ENV_SHARED_DATA_DIR = "DIGITAL_TWIN_SHARED_DIR"
ENV_LOCAL_CONFIG_DIR = "DIGITAL_TWIN_LOCAL_DIR"
ENV_CONFIG_FILE = "DIGITAL_TWIN_CONFIG"

# 配置文件路径
CONFIG_FILE_NAME = "deployment_config.json"


def get_shared_data_dir() -> str:
    """
    获取共享数据目录（多人版数据存储位置）
    
    优先级：
    1. 环境变量 DIGITAL_TWIN_SHARED_DIR
    2. 配置文件中的 shared_data_path
    3. 当前目录（默认）
    """
    # 1. 环境变量
    env_path = os.getenv(ENV_SHARED_DATA_DIR)
    if env_path:
        return os.path.abspath(env_path)
    
    # 2. 配置文件
    config = _load_deployment_config()
    if config and "shared_data_path" in config:
        return os.path.abspath(config["shared_data_path"])
    
    # 3. 默认：当前目录
    return os.getcwd()


def get_local_config_dir() -> str:
    """
    获取本地配置目录（个人版配置存储位置）
    
    优先级：
    1. 环境变量 DIGITAL_TWIN_LOCAL_DIR
    2. 配置文件中的 local_config_path
    3. 用户目录下的 DigitalTwin 文件夹
    """
    # 1. 环境变量
    env_path = os.getenv(ENV_LOCAL_CONFIG_DIR)
    if env_path:
        return os.path.abspath(os.path.expanduser(env_path))
    
    # 2. 配置文件
    config = _load_deployment_config()
    if config and "local_config_path" in config:
        return os.path.abspath(os.path.expanduser(config["local_config_path"]))
    
    # 3. 默认：用户目录下的 DigitalTwin
    user_home = os.path.expanduser("~")
    default_path = os.path.join(user_home, "DigitalTwin")
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
    """加载部署配置文件"""
    # 1. 环境变量指定的配置文件
    config_file_env = os.getenv(ENV_CONFIG_FILE)
    if config_file_env and os.path.exists(config_file_env):
        try:
            with open(config_file_env, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    
    # 2. 当前目录下的配置文件
    config_file = os.path.join(os.getcwd(), CONFIG_FILE_NAME)
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    
    return None


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
    """
    config = {
        "shared_data_path": os.path.abspath(shared_data_path),
        "local_config_path": local_config_path or os.path.join(
            os.path.expanduser("~"), "DigitalTwin"
        ),
        "version": "1.0",
        "description": "Digital Twin 部署配置"
    }
    
    save_file = save_path or os.path.join(os.getcwd(), CONFIG_FILE_NAME)
    try:
        with open(save_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception:
        return False
```

### Phase 2: 修改存储层支持路径配置

#### 2.1 修改 `store_org.py`

```python
# 在文件开头添加
from config_paths import get_shared_data_file

# 修改 PROFILE_FILE_MULTI 的定义
def _get_profile_file_multi() -> str:
    """获取多人版数据文件路径（支持配置）"""
    return get_shared_data_file()

# 替换所有 PROFILE_FILE_MULTI 的使用
# 原：os.path.exists(PROFILE_FILE_MULTI)
# 新：os.path.exists(_get_profile_file_multi())
```

#### 2.2 修改 `self_config.py`

```python
# 在文件开头添加
from config_paths import get_self_config_file, get_user_profile_file

# 修改 SELF_CONFIG_FILE 的定义
def _get_self_config_file() -> str:
    """获取个人配置文件路径（支持配置）"""
    return get_self_config_file()

# 替换所有 SELF_CONFIG_FILE 的使用
```

#### 2.3 修改 `store_single.py`

```python
# 在文件开头添加
from config_paths import get_user_profile_file

# 修改 PROFILE_FILE_SINGLE 的定义
def _get_profile_file_single() -> str:
    """获取个人版数据文件路径（支持配置）"""
    return get_user_profile_file()
```

### Phase 3: 创建部署工具脚本

**文件**：`deploy_setup.py`

```python
"""
部署设置工具
============
帮助管理员和用户快速配置部署环境。
"""

import os
import sys
from pathlib import Path
from config_paths import create_deployment_config


def setup_shared_deployment():
    """设置共享部署（管理员使用）"""
    print("=" * 60)
    print("Digital Twin - 共享部署设置")
    print("=" * 60)
    print()
    
    # 1. 选择共享数据位置
    print("步骤 1: 选择共享数据存储位置")
    print("提示：可以是网络驱动器路径，如：\\\\server\\shared\\digital_twin")
    print("      或本地共享文件夹路径")
    print()
    
    shared_path = input("请输入共享数据目录路径: ").strip()
    if not shared_path:
        print("❌ 路径不能为空")
        return False
    
    # 验证路径
    if not os.path.exists(shared_path):
        create = input(f"路径不存在，是否创建？(y/n): ").strip().lower()
        if create == 'y':
            try:
                os.makedirs(shared_path, exist_ok=True)
                print(f"✅ 已创建目录：{shared_path}")
            except Exception as e:
                print(f"❌ 创建目录失败：{e}")
                return False
        else:
            print("❌ 请先创建共享目录")
            return False
    
    # 2. 创建配置文件
    config_file = os.path.join(shared_path, "deployment_config.json")
    if create_deployment_config(shared_path, save_path=config_file):
        print(f"✅ 配置文件已创建：{config_file}")
    else:
        print(f"❌ 配置文件创建失败")
        return False
    
    # 3. 初始化共享数据文件（如果不存在）
    from store_org import _create_empty_org_store, save_org_store
    shared_data_file = os.path.join(shared_path, "user_profiles_multi.json")
    if not os.path.exists(shared_data_file):
        store = _create_empty_org_store()
        save_org_store(store)
        print(f"✅ 共享数据文件已初始化：{shared_data_file}")
    
    print()
    print("=" * 60)
    print("✅ 共享部署设置完成！")
    print("=" * 60)
    print()
    print("下一步：")
    print("1. 将配置文件路径告知所有用户")
    print(f"2. 用户运行：python deploy_setup.py --user --config {config_file}")
    print("3. 或用户手动设置环境变量：")
    print(f"   set DIGITAL_TWIN_SHARED_DIR={shared_path}")
    
    return True


def setup_user_deployment(config_file: str = None):
    """设置用户本地部署"""
    print("=" * 60)
    print("Digital Twin - 用户本地设置")
    print("=" * 60)
    print()
    
    # 1. 读取共享配置
    if config_file:
        import json
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
            shared_path = config.get("shared_data_path")
            print(f"✅ 已读取共享配置：{shared_path}")
        except Exception as e:
            print(f"❌ 读取配置文件失败：{e}")
            return False
    else:
        shared_path = input("请输入共享数据目录路径: ").strip()
        if not shared_path:
            print("❌ 路径不能为空")
            return False
    
    # 2. 验证共享路径可访问
    shared_data_file = os.path.join(shared_path, "user_profiles_multi.json")
    if not os.path.exists(shared_data_file):
        print(f"⚠️ 警告：共享数据文件不存在：{shared_data_file}")
        print("   请联系管理员初始化共享数据")
    
    # 3. 设置本地配置目录
    user_home = os.path.expanduser("~")
    local_path = os.path.join(user_home, "DigitalTwin")
    os.makedirs(local_path, exist_ok=True)
    print(f"✅ 本地配置目录：{local_path}")
    
    # 4. 创建用户配置文件
    user_config_file = os.path.join(local_path, "deployment_config.json")
    if create_deployment_config(shared_path, local_path, user_config_file):
        print(f"✅ 用户配置文件已创建：{user_config_file}")
    else:
        print(f"❌ 用户配置文件创建失败")
        return False
    
    print()
    print("=" * 60)
    print("✅ 用户本地设置完成！")
    print("=" * 60)
    print()
    print("现在可以启动应用：")
    print("  streamlit run app.py")
    print()
    print("首次使用请：")
    print("1. 在应用中绑定个人身份（个人版）")
    print("2. 或直接使用多人版功能")
    
    return True


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Digital Twin 部署设置工具")
    parser.add_argument("--admin", action="store_true", help="管理员模式：设置共享部署")
    parser.add_argument("--user", action="store_true", help="用户模式：设置本地配置")
    parser.add_argument("--config", type=str, help="配置文件路径（用户模式）")
    
    args = parser.parse_args()
    
    if args.admin:
        setup_shared_deployment()
    elif args.user:
        setup_user_deployment(args.config)
    else:
        print("请指定模式：--admin（管理员）或 --user（用户）")
        print()
        print("管理员模式：")
        print("  python deploy_setup.py --admin")
        print()
        print("用户模式：")
        print("  python deploy_setup.py --user --config <配置文件路径>")
```

### Phase 4: 创建启动脚本

#### Windows 启动脚本 (`start_app.bat`)

```batch
@echo off
REM Digital Twin 启动脚本（Windows）

REM 设置共享数据路径（根据实际情况修改）
set DIGITAL_TWIN_SHARED_DIR=\\server\shared\digital_twin

REM 设置本地配置路径（可选，默认用户目录）
REM set DIGITAL_TWIN_LOCAL_DIR=%USERPROFILE%\DigitalTwin

REM 启动应用
streamlit run app.py

pause
```

#### Linux/Mac 启动脚本 (`start_app.sh`)

```bash
#!/bin/bash
# Digital Twin 启动脚本（Linux/Mac）

# 设置共享数据路径（根据实际情况修改）
export DIGITAL_TWIN_SHARED_DIR="/mnt/shared/digital_twin"

# 设置本地配置路径（可选）
# export DIGITAL_TWIN_LOCAL_DIR="$HOME/DigitalTwin"

# 启动应用
streamlit run app.py
```

---

## 部署步骤

### 管理员部署步骤

1. **准备共享存储位置**
   ```
   创建网络共享文件夹或本地共享目录
   例如：\\server\shared\digital_twin
   或：C:\SharedData\DigitalTwin
   ```

2. **运行部署设置工具**
   ```bash
   python deploy_setup.py --admin
   ```
   按提示输入共享数据目录路径

3. **初始化共享数据**
   - 工具会自动创建 `user_profiles_multi.json`
   - 或手动导入初始团队数据

4. **分发配置文件**
   - 将 `deployment_config.json` 复制到共享位置
   - 告知用户配置文件路径

### 用户部署步骤

**方式一：使用部署工具（推荐）**

1. **运行用户设置**
   ```bash
   python deploy_setup.py --user --config \\server\shared\digital_twin\deployment_config.json
   ```

2. **启动应用**
   ```bash
   streamlit run app.py
   ```

**方式二：使用启动脚本**

1. **修改启动脚本**
   - 编辑 `start_app.bat`（Windows）或 `start_app.sh`（Linux）
   - 设置 `DIGITAL_TWIN_SHARED_DIR` 环境变量

2. **运行启动脚本**
   ```bash
   start_app.bat  # Windows
   # 或
   ./start_app.sh  # Linux/Mac
   ```

**方式三：手动设置环境变量**

1. **Windows**
   ```cmd
   set DIGITAL_TWIN_SHARED_DIR=\\server\shared\digital_twin
   streamlit run app.py
   ```

2. **Linux/Mac**
   ```bash
   export DIGITAL_TWIN_SHARED_DIR="/mnt/shared/digital_twin"
   streamlit run app.py
   ```

---

## 数据同步机制

### 多人版数据（共享）

- **存储位置**：共享网络位置或共享文件夹
- **访问方式**：所有用户读写同一文件
- **冲突处理**：
  - 使用文件锁机制（如果支持）
  - 或采用"最后写入获胜"策略
  - 建议：重要操作前先刷新数据

### 个人版数据（独立）

- **存储位置**：每个用户的本地目录
- **绑定机制**：`self_config.json` 存储 `self_person_id`
- **数据同步**：
  - 个人版修改 → 自动同步到共享数据（OrgStore）
  - 读取时从共享数据读取，保证一致性

---

## 权限管理建议

### 共享文件夹权限

- **读取权限**：所有用户
- **写入权限**：所有用户（或特定管理员组）
- **建议**：定期备份 `user_profiles_multi.json`

### 本地配置权限

- **读取/写入**：仅当前用户
- **位置**：用户目录下，自动创建

---

## 测试验证

### 测试场景

1. **多用户同时访问**
   - 用户A和用户B同时打开应用
   - 验证都能看到相同的多人版数据

2. **个人版绑定**
   - 用户A绑定 person_id=p1
   - 用户B绑定 person_id=p2
   - 验证各自只能修改自己的信息

3. **数据同步**
   - 用户A修改个人信息
   - 验证修改同步到共享数据
   - 用户B刷新后能看到更新

4. **冲突处理**
   - 两个用户同时修改同一人的信息
   - 验证最后写入生效（或提示冲突）

---

## 故障排除

### 常见问题

1. **无法访问共享文件夹**
   - 检查网络连接
   - 验证共享路径是否正确
   - 确认有读写权限

2. **个人配置丢失**
   - 检查本地配置目录是否存在
   - 验证 `self_config.json` 文件

3. **数据不同步**
   - 检查共享数据文件路径配置
   - 验证文件权限
   - 查看应用日志

---

## 安全建议

1. **共享数据备份**
   - 定期备份 `user_profiles_multi.json`
   - 建议每日自动备份

2. **访问控制**
   - 限制共享文件夹访问权限
   - 使用只读用户（如果需要）

3. **数据加密**（可选）
   - 敏感信息加密存储
   - API Key 不存储在共享数据中

---

## 后续优化方向

1. **数据库支持**
   - 迁移到 SQLite/PostgreSQL
   - 支持事务和并发控制

2. **版本控制**
   - 数据变更历史记录
   - 回滚功能

3. **Web 服务部署**
   - 部署为 Web 服务
   - 统一数据访问入口

---

## 总结

本部署方案实现了：
- ✅ 多人版数据共享（统一管理）
- ✅ 个人版数据独立（用户绑定）
- ✅ 灵活的配置方式（环境变量/配置文件）
- ✅ 易于部署和维护

**关键文件**：
- `config_paths.py` - 路径配置管理
- `deploy_setup.py` - 部署设置工具
- `start_app.bat` / `start_app.sh` - 启动脚本
- `deployment_config.json` - 部署配置文件

---

**文档版本**：v1.0  
**最后更新**：2025-02-06
