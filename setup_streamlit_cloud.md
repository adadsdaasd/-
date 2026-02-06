# Streamlit Cloud 部署详细步骤

## 📋 前置准备

1. GitHub 账号（如果没有，免费注册：https://github.com）
2. 项目代码已准备好

---

## 步骤 1：创建 GitHub 仓库

### 1.1 登录 GitHub

访问 https://github.com 并登录

### 1.2 创建新仓库

1. 点击右上角 `+` → `New repository`
2. 填写信息：
   - **Repository name**：`digital-twin-app`（或您喜欢的名字）
   - **Description**：`Digital Twin - 数字分身应用`（可选）
   - **Visibility**：
     - `Public`：代码公开，完全免费
     - `Private`：代码私有，需要 GitHub Pro（付费）或使用其他平台
   - **不要**勾选 `Add a README file`（我们已有代码）
3. 点击 `Create repository`

### 1.3 记录仓库地址

创建后会显示仓库地址，类似：
```
https://github.com/YOUR_USERNAME/digital-twin-app.git
```
记住这个地址，下一步会用到。

---

## 步骤 2：上传代码到 GitHub

### 方式一：使用 Git 命令行（推荐）

在项目目录下打开命令行：

```bash
# 1. 初始化 Git（如果还没有）
git init

# 2. 添加所有文件
git add .

# 3. 提交
git commit -m "Initial commit: Digital Twin app"

# 4. 添加远程仓库（替换 YOUR_USERNAME 为您的 GitHub 用户名）
git remote add origin https://github.com/YOUR_USERNAME/digital-twin-app.git

# 5. 推送代码
git branch -M main
git push -u origin main
```

**如果提示需要登录**：
- GitHub 现在使用 Personal Access Token
- 访问：https://github.com/settings/tokens
- 生成新 token（权限：repo）
- 使用 token 作为密码

### 方式二：使用 GitHub Desktop（图形界面）

1. **下载安装**
   - 访问：https://desktop.github.com/
   - 下载并安装 GitHub Desktop

2. **登录**
   - 打开 GitHub Desktop
   - 使用 GitHub 账号登录

3. **添加仓库**
   - 点击 `File` → `Add Local Repository`
   - 选择项目目录：`C:\Users\28252\Desktop\vibecoding`
   - 点击 `Add repository`

4. **提交并推送**
   - 在左侧填写提交信息：`Initial commit: Digital Twin app`
   - 点击 `Commit to main`
   - 点击 `Publish repository`（首次）或 `Push origin`（后续）

### 方式三：直接在网页上传（最简单）

1. 在 GitHub 仓库页面，点击 `uploading an existing file`
2. 拖拽项目文件夹中的所有文件
3. 填写提交信息
4. 点击 `Commit changes`

---

## 步骤 3：部署到 Streamlit Cloud

### 3.1 访问 Streamlit Cloud

1. 打开：https://streamlit.io/cloud
2. 点击 `Sign up` 或 `Get started`

### 3.2 使用 GitHub 登录

1. 点击 `Sign in with GitHub`
2. 授权 Streamlit Cloud 访问您的 GitHub
3. 选择授权范围（建议选择所有仓库）

### 3.3 创建新应用

1. 点击 `New app` 按钮
2. 填写信息：
   - **Repository**：选择 `digital-twin-app`
   - **Branch**：选择 `main`
   - **Main file path**：`app.py`
   - **App URL**：可以自定义（如果可用）
     - 例如：`my-digital-twin`
     - 最终链接：`https://my-digital-twin.streamlit.app`
3. 点击 `Deploy!`

### 3.4 等待部署

- 首次部署需要 1-3 分钟
- 可以看到部署日志
- 部署完成后会显示：`Your app is live!`

### 3.5 获取公网链接

部署完成后，会显示您的应用链接：
```
https://your-app-name.streamlit.app
```

**这个链接可以分享给任何人！**

---

## 步骤 4：配置环境变量（可选）

如果应用需要 API Key 等敏感信息：

1. 在 Streamlit Cloud 应用页面
2. 点击右上角 `⚙️ Settings`
3. 找到 `Secrets` 部分
4. 点击 `Edit secrets`
5. 添加环境变量：
   ```toml
   [default]
   DEEPSEEK_API_KEY = "sk-your-api-key-here"
   ```
6. 点击 `Save`

**在代码中使用**：
```python
import os
api_key = os.getenv("DEEPSEEK_API_KEY")
# 或使用 streamlit secrets
import streamlit as st
api_key = st.secrets.get("DEEPSEEK_API_KEY", "")
```

---

## 步骤 5：更新应用

每次修改代码后：

```bash
git add .
git commit -m "Update: 描述您的修改"
git push
```

Streamlit Cloud 会自动检测并重新部署！

---

## ✅ 验证部署

1. **访问链接**
   - 打开浏览器
   - 访问您的 Streamlit Cloud 链接
   - 例如：`https://your-app-name.streamlit.app`

2. **测试功能**
   - 检查页面是否正常加载
   - 测试各个功能是否正常

3. **分享链接**
   - 将链接分享给其他用户
   - 他们可以在任何地方访问

---

## 🎉 完成！

现在您的应用已经：
- ✅ 部署到公网
- ✅ 可以通过链接访问
- ✅ 支持多用户同时使用
- ✅ 完全免费

**公网链接示例**：
```
https://your-app-name.streamlit.app
```

任何人都可以通过这个链接访问您的应用！

---

## 🔧 常见问题

### Q: 部署失败怎么办？

**A:** 检查：
1. `app.py` 是否在根目录
2. `requirements.txt` 是否存在且正确
3. 查看部署日志中的错误信息

### Q: 如何更新应用？

**A:** 
```bash
git add .
git commit -m "Update"
git push
```
Streamlit Cloud 会自动重新部署。

### Q: 可以绑定自定义域名吗？

**A:** Streamlit Cloud 免费版不支持自定义域名，但链接是永久的。

### Q: 数据存储在哪里？

**A:** Streamlit Cloud 不提供持久化存储。如果需要数据持久化，建议：
- 使用数据库（如 Supabase、Firebase）
- 使用云存储（如 AWS S3、Google Cloud Storage）

---

**需要帮助？** 查看 Streamlit Cloud 文档：https://docs.streamlit.io/streamlit-cloud
